#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <thread>
#include <mutex>
#include <cmath>
#include <iomanip>
#include <cstring>
#include <algorithm>
#include <filesystem>

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
    std::vector<std::string> lines;
    std::string line;
    while (std::getline(file, line))
        if (!line.empty() && line[0] != '#') lines.emplace_back(std::move(line));

    size_t n = lines.size();
    std::vector<GFFFeature> features;
    std::mutex mtx;
    std::vector<std::thread> threads;

    auto worker = [&](size_t beg, size_t end) {
        std::vector<GFFFeature> local;
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

            double scr = score == "." ? 0.0 : std::stod(score);

            local.push_back({std::move(seq), std::move(type),
                            std::stoi(st), std::stoi(en),
                            strand[0], scr});
        }
        std::lock_guard<std::mutex> lock(mtx);
        features.insert(features.end(), local.begin(), local.end());
    };

    size_t chunk = (n + n_threads - 1) / n_threads;
    for (unsigned i = 0; i < n_threads; ++i) {
        size_t beg = i * chunk, end = std::min(n, beg + chunk);
        threads.emplace_back(worker, beg, end);
    }
    for (auto &t : threads) t.join();
    return features;
}

void evaluate_auc(const std::vector<GFFFeature>& refs,
                  const std::vector<GFFFeature>& preds,
                  const std::string& out_path) {

    std::vector<std::pair<double, double>> roc_points;  // (FPR, TPR)
    std::vector<std::pair<double, double>> prc_points;  // (Recall, Precision)

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

    std::vector<std::pair<double, bool>> scores;
    for (const auto& f : preds) {
        if (f.feature_type != "gene") continue;
        int id = get_seqid_id(f.seqid);
        for (int p = f.start; p <= f.end; ++p) {
            uint64_t enc = encode_nuc(id, p, f.strand);
            scores.emplace_back(f.score, ref_nucs.count(enc));
        }
    }

    std::sort(scores.begin(), scores.end(), [](auto& a, auto& b) {
        return a.first > b.first;
    });

    double tp = 0, fp = 0;
    double prev_tpr = 0.0, prev_fpr = 0.0;
    double prev_recall = 0.0;
    double auc = 0.0, aucpr = 0.0;

    int P = std::count_if(scores.begin(), scores.end(), [](auto& p) { return p.second; });
    int N = scores.size() - P;

    for (size_t i = 0; i < scores.size(); ++i) {
        if (scores[i].second) tp++;
        else fp++;

        double tpr = (P > 0) ? tp / P : 0.0;
        double fpr = (N > 0) ? fp / N : 0.0;
        double precision = (tp + fp > 0) ? tp / (tp + fp) : 1.0;
        double recall = tpr;

        // Store points
        roc_points.emplace_back(fpr, tpr);
        prc_points.emplace_back(recall, precision);

        // AUC-ROC: trapezoid integration over (fpr, tpr)
        auc += (fpr - prev_fpr) * (tpr + prev_tpr) / 2;

        // AUC-PRC: stepwise area
        aucpr += (recall - prev_recall) * precision;

        prev_fpr = fpr;
        prev_tpr = tpr;
        prev_recall = recall;
    }

    // Write AUC summary
    std::ofstream out(out_path + "_auc.csv");
    out << "AUC_ROC,AUC_PRC\n";
    out << std::fixed << std::setprecision(4) << auc << "," << aucpr << "\n";

    // Write ROC curve points
    std::ofstream roc_out(out_path + "_roc.csv");
    roc_out << "FPR,TPR\n";
    for (auto& p : roc_points)
        roc_out << std::fixed << std::setprecision(6) << p.first << "," << p.second << "\n";

    // Write PRC curve points
    std::ofstream prc_out(out_path + "_prc.csv");
    prc_out << "Recall,Precision\n";
    for (auto& p : prc_points)
        prc_out << std::fixed << std::setprecision(6) << p.first << "," << p.second << "\n";
}


std::vector<GFFFeature> read_txt_format(const std::string& file_path) {
    std::ifstream file(file_path);

    std::vector<GFFFeature> features;
    std::string line;

    while (std::getline(file, line)) {
        if (line.empty() || line.find("Label:") == std::string::npos) continue;

        std::string chromosome, strand, type;
        std::string start_str, end_str;
        int start = 0, end = 0;

        std::istringstream ss(line);
        std::string token;

        while (ss >> token) {
            if (token == "Chromosome:") {
                ss >> chromosome;
                if (!chromosome.empty() && chromosome[0] == '>')
                    chromosome = chromosome.substr(1);
                if (!chromosome.empty() && chromosome.back() == ',')
                    chromosome.pop_back();
            } else if (token == "Strand:") {
                ss >> strand;
                if (!strand.empty() && strand.back() == ',')
                    strand.pop_back();
            } else if (token == "Label:") {
                ss >> type;
                if (!type.empty() && type.back() == ',')
                    type.pop_back();
            } else if ((token == "Start:") || (token == "Start_Center:")) {
                ss >> start_str;
                if (!start_str.empty() && start_str.back() == ',')
                    start_str.pop_back();
                start = (start_str != "None") ? std::stoi(start_str) : -1;
            } else if ((token == "End:") || (token == "End_Center:")) {
                ss >> end_str;
                if (!end_str.empty() && end_str.back() == ',')
                    end_str.pop_back();
                end = (end_str != "None") ? std::stoi(end_str) : -1;
            }
        }

        if (!chromosome.empty() && !type.empty() && start != -1 && end != -1) {
            char strand_char = (strand == "reverse") ? '-' : '+';
            features.push_back({chromosome, type, start, end, strand_char});
        }
    }

    return features;
}

void compute_nucleotide_overlap(const std::vector<GFFFeature>& refs,
                                const std::vector<GFFFeature>& preds,
                                const std::string& label,
                                std::ostream& out) {
    std::unordered_map<std::string, int> seqid_to_id;
    int next_id = 0;
    auto get_seqid_id = [&](const std::string& s) -> int {
        auto it = seqid_to_id.find(s);
        if (it != seqid_to_id.end()) return it->second;
        return seqid_to_id[s] = next_id++;
    };

    std::unordered_set<uint64_t> ref_nucs, pred_nucs;

    auto fill_set = [&](const std::vector<GFFFeature>& data,
                        std::unordered_set<uint64_t>& target,
                        const std::string& feat) {
        for (const auto& f : data) {
            if (f.feature_type != feat) continue;
            int id = get_seqid_id(f.seqid);
            for (int p = f.start; p <= f.end; ++p)
                target.insert(encode_nuc(id, p, f.strand));
        }
    };

    fill_set(refs, ref_nucs, label);
    fill_set(preds, pred_nucs, label);

    int TP = 0;
    for (const auto& n : pred_nucs)
        if (ref_nucs.count(n)) ++TP;

    int FN = ref_nucs.size() - TP;
    int FP = pred_nucs.size() - TP;
    double sens = (TP + FN) ? 100.0 * TP / (TP + FN) : 0.0;
    double spec = (TP + FP) ? 100.0 * TP / (TP + FP) : 0.0;

    out << label << "_nucleotide," << TP << ',' << FP << ',' << FN << ','
        << std::fixed << std::setprecision(2) << sens << ',' << spec << '\n';
}

void evaluate_and_write_csv(const std::vector<GFFFeature>& refs,
                            const std::vector<GFFFeature>& preds,
                            std::ostream& out) {
    const std::unordered_set<std::string> valid_labels = {"gene", "mRNA", "CDS", "exon"};

    std::unordered_map<std::string, std::unordered_set<std::string>> ref_by, pred_by;

    auto encode = [](const GFFFeature& f) {
        return f.seqid + ":" + std::to_string(f.start) + "-" + std::to_string(f.end) + ":" + f.strand;
    };

    for (const auto& f : refs)
        if (valid_labels.count(f.feature_type))
            ref_by[f.feature_type].insert(encode(f));

    for (const auto& f : preds)
        if (valid_labels.count(f.feature_type))
            pred_by[f.feature_type].insert(encode(f));

    std::vector<std::string> all_labels;
    for (const auto& kv : ref_by) all_labels.push_back(kv.first);
    for (const auto& kv : pred_by)
        if (ref_by.find(kv.first) == ref_by.end())
            all_labels.push_back(kv.first);

    out << "label,tp,fp,fn,sensitivity,specificity\n";

    for (const auto& label : all_labels) {
        const auto& ref_set = ref_by[label];
        const auto& pred_set = pred_by[label];

        std::unordered_set<std::string> intersection;
        for (const auto& s : pred_set)
            if (ref_set.count(s)) intersection.insert(s);

        int TP = intersection.size();
        int FN = ref_set.size() - TP;
        int FP = pred_set.size() - TP;

        double sens = (TP + FN) ? 100.0 * TP / (TP + FN) : 0.0;
        double spec = (TP + FP) ? 100.0 * TP / (TP + FP) : 0.0;

        out << label << ',' << TP << ',' << FP << ',' << FN << ','
            << std::fixed << std::setprecision(2)
            << sens << ',' << spec << '\n';
    }

    compute_nucleotide_overlap(refs, preds, "CDS", out);
    compute_nucleotide_overlap(refs, preds, "gene", out);
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <ref> <pred or folder> [--threads N]\n";
        return 1;
    }

    std::string ref_file = argv[1], pred_input = argv[2], out_file;
    unsigned threads = std::thread::hardware_concurrency();

    for (int i = 3; i < argc; ++i) {
        if (std::strcmp(argv[i], "--threads") == 0 && i+1 < argc) {
            threads = std::stoi(argv[++i]);
        } else {
            std::cerr << "Unknown argument: " << argv[i] << '\n';
            return 1;
        }
    }

    std::vector<GFFFeature> refs = parse_gff_parallel(ref_file, threads);

    namespace fs = std::filesystem;
    fs::path pred_path(pred_input);

    if (fs::is_directory(pred_path)) {
        

        for (const auto& entry : fs::directory_iterator(pred_path)) {
            if (!entry.is_regular_file()) continue;
            auto file_path = entry.path();
            
            if (file_path.extension() == ".csv") continue;
            
            std::string base_name = file_path.stem().string();

            std::cout << "Processing " << file_path.filename() << "\n";

            std::vector<GFFFeature> preds;
            if (file_path.extension() == ".txt") {
                preds = read_txt_format(file_path.string());
                evaluate_auc(refs, preds, (file_path.parent_path() / base_name).string());
            } else {
                preds = parse_gff_parallel(file_path.string(), threads);
            }

            std::ofstream ofs(file_path.parent_path() / (base_name + ".csv"));
            evaluate_and_write_csv(refs, preds, ofs);

            if (base_name.rfind("augustus_", 0) == 0) {
                evaluate_auc(refs, preds, (file_path.parent_path() / base_name).string());
            }
        }
    }
    else {
        std::cout << "Processing single file: " << pred_input << "\n";
        std::vector<GFFFeature> preds;
        fs::path p(pred_input);
        std::string base_name = p.stem().string();

        if (p.extension() == ".txt") {
            preds = read_txt_format(pred_input);
            evaluate_auc(refs, preds, (p.parent_path() / base_name).string());
        } else {
            preds = parse_gff_parallel(pred_input, threads);
        }

        fs::path csv_file = p.parent_path() / (base_name + ".csv");
        std::ofstream ofs(csv_file);
        evaluate_and_write_csv(refs, preds, ofs);

        // always check base name for augustus_
        if (base_name.rfind("augustus_", 0) == 0){
            evaluate_auc(refs, preds, (p.parent_path() / base_name).string());
        }
    }

    return 0;
}
