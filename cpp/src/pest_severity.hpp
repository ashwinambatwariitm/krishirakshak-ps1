/*
 * pest_severity.hpp - pest severity level for one photo, from the insects found by the pest detector.
 *
 * Problem statement: "classify severity levels" for diseases and pests. A photo cannot measure infestation of a
 * field, so the level here describes THIS photo only, and every result quotes the published scouting method that
 * the farmer should use before deciding to spray (NIPHM AESA-based IPM package for tomato, TNAU IPM), plus the
 * published economic threshold where one exists.
 *
 * Level of each pest topic in the photo (project rule, not an agronomic standard; see docs/SEVERITY.md):
 *   colony insects (aphids, whitefly, mites, thrips, leafhoppers, mealybug): 1-4 low, 5-19 moderate, 20+ high
 *     small insects living in groups: a few are common, a dense colony on one leaf is serious;
 *   chewing larvae (caterpillars, fruit borer, Spodoptera, cutworm, Tuta): 1-2 moderate, 3+ high
 *     a single larva can already matter: TNAU's threshold for fruit borer is "single larva per plant";
 *   species uncertain (insect_other): colony bands, reported as uncertain.
 * Counts come from the pest detector (YOLOv8n, IP102); among tomato pests only aphids are identified reliably,
 * other insects are reported as "insect, species uncertain".
 */
#pragma once

#include "knowledge_base.hpp"
#include "pest_detector.hpp"

#include <json.hpp>

#include <string>
#include <vector>

namespace kr {

struct PestSeverity {
    std::string topic;            // knowledge-base pest topic (aphids, insect_other, ...)
    std::string group;            // colony, chewing, uncertain
    int count = 0;                // insects of this topic detected in the photo
    double boxShare = 0.0;        // share of the photo covered by their boxes (technical panel)
    std::string level;            // low, moderate, high
};

// One entry per pest topic found in the photo, most severe first.
std::vector<PestSeverity> pestSeverity(const std::vector<PestDetection>& pests, const KnowledgeBase& kb,
                                       int imageWidth, int imageHeight);

// JSON for the result: level, count, basis, and the quoted scouting method / economic threshold extracts.
nlohmann::json pestSeverityJson(const std::vector<PestSeverity>& sev, const KnowledgeBase& kb, const std::string& lang);

}  // namespace kr
