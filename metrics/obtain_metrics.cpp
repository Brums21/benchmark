#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <cstring>

struct GFFFeature {
    std::string seqid;
    std::string feature_type;
    int start;
    int end;
    char strand;
    double score = 0.0;
};

inline uint64_t encode_nuc(int seqid_id, int pos, char strand) {
    return (static_cast<uint64_t>(seqid_id) << 32) |
           (static_cast<uint64_t>(pos) << 1) |
           (strand == '+' ? 1 : 0);
}

std::vector<GFFFeature> parse_gff_parallel(const std::string& file_path, unsigned n_threads) {
    std::ifstream file(file_path);
    if (!file) {
        throw std::runtime_error("Cannot open GFF file: " + file_path);
    }

    std::vector<std::string> lines;
    std::string line;
    lines.reserve(1 << 20);
    while (std::getline(file, line)) {
        if (!line.empty() && line[0] != '#') lines.emplace_back(std::move(line));
    }

    size_t n = lines.size();
    std::vector<GFFFeature> features;
    features.reserve(n);
    std::mutex mtx;
    std::vector<std::thread> threads;

    auto worker = [&](size_t beg, size_t end) {
        std::vector<GFFFeature> local;
        local.reserve(end > beg ? (end - beg) : 0);
        for (size_t i = beg; i < end; ++i) {
            std::istringstream ss(lines[i]);
            std::string seq, src, type, st, en, score, strand, phase, attrs;
            if (!(std::getline(ss, seq, '\t') &&
                  std::getline(ss, src, '\t') &&
                  std::getline(ss, type, '\t') &&
                  std::getline(ss, st, '\t') &&
                  std::getline(ss, en, '\t') &&
                  std::getline(ss, score, '\t') &&
                  std::getline(ss, strand, '\t') &&
                  std::getline(ss, phase, '\t') &&
                  std::getline(ss, attrs))) continue;

            double scr = (score == "." ? 0.0 : std::stod(score));
            int s = std::stoi(st);
            int e = std::stoi(en);
            if (s > e) std::swap(s, e);

            local.push_back({std::move(seq), std::move(type), s, e, strand.empty() ? '+' : strand[0], scr});
        }
        std::lock_guard<std::mutex> lock(mtx);
        features.insert(features.end(), local.begin(), local.end());
    };

    if (n_threads == 0) n_threads = 1;
    size_t chunk = (n + n_threads - 1) / n_threads;
    for (unsigned i = 0; i < n_threads; ++i) {
        size_t beg = i * chunk, end = std::min(n, beg + chunk);
        threads.emplace_back(worker, beg, end);
    }
    for (auto& t : threads) t.join();
    return features;
}

void evaluate_auc(const std::vector<GFFFeature>& refs,
                  const std::vector<GFFFeature>& preds,
                  const std::string& out_path_noext) {
    // Build nucleotide sets and scores for genes only
    std::unordered_map<std::string, int> seqid_to_id;
    int next_id = 0;
    auto get_seqid_id = [&](const std::string& s) -> int {
        auto it = seqid_to_id.find(s);
        if (it != seqid_to_id.end()) return it->second;
        return seqid_to_id[s] = next_id++;
    };

    std::unordered_set<uint64_t> ref_nucs;
    for (const auto& f : refs) {
        if (f.feature_type != "gene") continue;
        int id = get_seqid_id(f.seqid);
        for (int p = f.start; p <= f.end; ++p)
            ref_nucs.insert(encode_nuc(id, p, f.strand));
    }

    std::vector<std::pair<double, bool>> scores;  // (score, is_positive)
    scores.reserve(ref_nucs.size());
    for (const auto& f : preds) {
        if (f.feature_type != "gene") continue;
        int id = get_seqid_id(f.seqid);
        for (int p = f.start; p <= f.end; ++p) {
            uint64_t enc = encode_nuc(id, p, f.strand);
            scores.emplace_back(f.score, ref_nucs.count(enc) != 0);
        }
    }

    if (scores.empty()) {
        std::ofstream out(out_path_noext + "_auc.csv");
        out << "AUC_ROC,AUC_PRC\n0.0000,0.0000\n";
        std::ofstream roc(out_path_noext + "_roc.csv"); roc << "FPR,TPR\n";
        std::ofstream prc(out_path_noext + "_prc.csv"); prc << "Recall,Precision\n";
        return;
    }

    std::sort(scores.begin(), scores.end(), [](auto& a, auto& b) { return a.first > b.first; });

    double tp = 0, fp = 0;
    double prev_tpr = 0.0, prev_fpr = 0.0, prev_recall = 0.0;
    double auc = 0.0, aucpr = 0.0;

    int P = 0;
    for (auto& s : scores) if (s.second) ++P;
    int N = static_cast<int>(scores.size()) - P;

    std::vector<std::pair<double,double>> roc_points;
    std::vector<std::pair<double,double>> prc_points;
    roc_points.reserve(scores.size());
    prc_points.reserve(scores.size());

    for (size_t i = 0; i < scores.size(); ++i) {
        if (scores[i].second) ++tp; else ++fp;

        double tpr = (P > 0) ? tp / P : 0.0;
        double fpr = (N > 0) ? fp / N : 0.0;
        double precision = (tp + fp > 0) ? tp / (tp + fp) : 1.0;
        double recall = tpr;

        roc_points.emplace_back(fpr, tpr);
        prc_points.emplace_back(recall, precision);
        auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2.0;
        aucpr += (recall - prev_recall) * precision;

        prev_fpr = fpr;
        prev_tpr = tpr;
        prev_recall = recall;
    }

    std::ofstream out(out_path_noext + "_auc.csv");
    out << "AUC_ROC,AUC_PRC\n";
    out << std::fixed << std::setprecision(4) << auc << "," << aucpr << "\n";

    std::ofstream roc_out(out_path_noext + "_roc.csv");
    roc_out << "FPR,TPR\n";
    for (auto& p : roc_points)
        roc_out << std::fixed << std::setprecision(6) << p.first << "," << p.second << "\n";

    std::ofstream prc_out(out_path_noext + "_prc.csv");
    prc_out << "Recall,Precision\n";
    for (auto& p : prc_points)
        prc_out << std::fixed << std::setprecision(6) << p.first << "," << p.second << "\n";
}

void write_gene_nucleotide_csv(const std::vector<GFFFeature>& refs,
                               const std::vector<GFFFeature>& preds,
                               const std::filesystem::path& csv_path) {
    
    std::unordered_map<std::string, int> seqid_to_id;
    int next_id = 0;
    auto get_seqid_id = [&](const std::string& s) -> int {
        auto it = seqid_to_id.find(s);
        if (it != seqid_to_id.end()) return it->second;
        return seqid_to_id[s] = next_id++;
    };

    std::unordered_set<uint64_t> ref_nucs, pred_nucs;

    auto fill_gene = [&](const std::vector<GFFFeature>& data,
                         std::unordered_set<uint64_t>& target) {
        for (const auto& f : data) {
            if (f.feature_type != "gene") continue;
            int id = get_seqid_id(f.seqid);
            for (int p = f.start; p <= f.end; ++p)
                target.insert(encode_nuc(id, p, f.strand));
        }
    };

    fill_gene(refs, ref_nucs);
    fill_gene(preds, pred_nucs);

    int TP = 0;
    for (const auto& n : pred_nucs)
        if (ref_nucs.count(n)) ++TP;

    int FN = static_cast<int>(ref_nucs.size()) - TP;
    int FP = static_cast<int>(pred_nucs.size()) - TP;
    double sens = (TP + FN) ? 100.0 * TP / (TP + FN) : 0.0;
    double spec = (TP + FP) ? 100.0 * TP / (TP + FP) : 0.0;

    std::ofstream out(csv_path);
    out << "label,tp,fp,fn,sensitivity,specificity\n";
    out << "gene_nucleotide," << TP << ',' << FP << ',' << FN << ','
        << std::fixed << std::setprecision(2) << sens << ',' << spec << '\n';
}

static inline bool is_gff_like(const std::filesystem::path& p) {
    std::string ext = p.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return (ext == ".gff" || ext == ".gff3");
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0]
                  << " <reference.gff[3]> <predictions file or folder> [--output_folder path] [--threads N] [--print-auc] \n";
        return 1;
    }

    namespace fs = std::filesystem;

    std::string ref_file = argv[1];
    std::string pred_input = argv[2];
    unsigned threads = std::thread::hardware_concurrency();
    std::string output_folder;
    bool print_auc = false;

    for (int i = 3; i < argc; ++i) {
        if (std::strcmp(argv[i], "--threads") == 0 && i + 1 < argc) {
            threads = static_cast<unsigned>(std::stoul(argv[++i]));
        } else if (std::strcmp(argv[i], "--output_folder") == 0 && i + 1 < argc) {
            output_folder = argv[++i];
        } else if (std::strcmp(argv[i], "--print_auc") == 0) {
            print_auc = true;
        } else {
            std::cerr << "Unknown argument: " << argv[i] << '\n';
            return 1;
        }
    }

    if (!is_gff_like(ref_file)) {
        std::cerr << "Reference must be GFF/GFF3: " << ref_file << "\n";
        return 1;
    }

    std::vector<GFFFeature> refs;
    try {
        refs = parse_gff_parallel(ref_file, threads);
    } catch (const std::exception& e) {
        std::cerr << "Error parsing reference: " << e.what() << "\n";
        return 1;
    }

    fs::path pred_path(pred_input);

    if (fs::is_directory(pred_path)) {
        fs::path out_dir = output_folder.empty() ? pred_path : fs::path(output_folder);
        if (!output_folder.empty()) fs::create_directories(out_dir);

        for (const auto& entry : fs::directory_iterator(pred_path)) {
            if (!entry.is_regular_file()) continue;
            const fs::path file_path = entry.path();

            if (!is_gff_like(file_path)) {
                continue;
            }

            const std::string base_name = file_path.stem().string();

            fs::path csv_file = out_dir / (base_name + ".csv");
            fs::path auc_base = (out_dir / base_name).string();

            std::cout << "Processing " << file_path.filename().string() << "\n";

            std::vector<GFFFeature> preds;
            try {
                preds = parse_gff_parallel(file_path.string(), threads);
            } catch (const std::exception& e) {
                std::cerr << "  Skipping (parse error): " << e.what() << "\n";
                continue;
            }

            write_gene_nucleotide_csv(refs, preds, csv_file);

            if (print_auc) {
                evaluate_auc(refs, preds, auc_base.string());
            }
        }
    } else {
        if (!is_gff_like(pred_path)) {
            std::cerr << "Predictions must be GFF/GFF3: " << pred_input << "\n";
            return 1;
        }

        std::cout << "Processing single file: " << pred_input << "\n";
        const std::string base_name = pred_path.stem().string();

        fs::path out_dir = output_folder.empty() ? pred_path.parent_path()
                                                 : fs::path(output_folder);
        if (!output_folder.empty()) fs::create_directories(out_dir);

        fs::path csv_file = out_dir / (base_name + ".csv");
        fs::path auc_base = (out_dir / base_name).string();

        std::vector<GFFFeature> preds;
        try {
            preds = parse_gff_parallel(pred_input, threads);
        } catch (const std::exception& e) {
            std::cerr << "Error parsing predictions: " << e.what() << "\n";
            return 1;
        }

        write_gene_nucleotide_csv(refs, preds, csv_file);

        if (print_auc) {
            evaluate_auc(refs, preds, auc_base.string());
        }
    }

    return 0;
}
