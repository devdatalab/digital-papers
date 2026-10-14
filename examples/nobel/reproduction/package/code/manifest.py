#!/usr/bin/env python3
"""The list of analysis scripts in this package, their run order, and what
each one reproduces.

Why this file exists:
    run_all.py needs to know which scripts to run and which files each one
    writes, so it can re-run the whole package and check the results. Keeping
    that list in one place means adding a script is a one-line change here.
    The `exhibits` field records the PDF figure/table labels; `panels` records
    the shared supplementary-panel numbering in reading order. Both mappings
    are presented in code/README.md.

    No script currently reads another script's output, so the order below is
    for readability only (main text first, then appendix, then supplementary).

Upstream dependencies:
    None. Imported by run_all.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Script:
    """One analysis script.

    entry:    path to the .py file, relative to code/.
    outputs:  file names the script writes into its own output/ folder.
    exhibits: the PDF exhibits it reproduces, or "Supplementary".
    panels:   supplementary panel ids in the shared reading-order sequence.
    """

    entry: str
    outputs: tuple[str, ...]
    exhibits: str
    panels: tuple[str, ...] = ()

    @property
    def path(self) -> Path:
        return CODE_DIR / self.entry

    @property
    def output_dir(self) -> Path:
        return self.path.parent / "output"


SCRIPTS: tuple[Script, ...] = (
    # Main text.
    Script("rank_histograms/rank_histograms.py", ("rank_histograms.json",), "Figure 1"),
    Script("main_binscatter_ranks/main_binscatter_ranks.py", ("binscatter_ranks.json",),
           "Figure 2, Figure A2", ("A12",)),
    Script("main_spec/main_spec.py", ("main_spec.json",), "Table 1, Table A7", ("A15",)),
    Script("heterogeneity_spec/heterogeneity_spec.py", ("heterogeneity_spec.json",), "Table 2"),
    Script("parent_field_match/parent_field_perm_test.py", ("parent_field_perm_test.json",),
           "Figure 3, Table 3, Figure A4", ("A18",)),
    # Appendix.
    Script("most_common_occupations/most_common_occupations.py",
           ("most_common_occupations.json",), "Figure A1", ("A5",)),
    Script("other_rank_functions/other_rank_functions.py", ("other_rank_functions.json",),
           "Figure A3", ("A13",)),
    Script("parent_field_match/parent_field_match_graphs.py",
           ("parent_field_match_shares.json",), "Figure A5", ("A19",)),
    Script("occ_shares/occ_shares.py",
           ("occ_shares_10group.json", "occ_shares_25group.json",
            "occ_shares_occ1950_list.json", "occupation_list.json"),
           "Table A2, Table A3", ("A9", "A10", "A17")),
    Script("main_robust/main_robust.py", ("main_robust.json",), "Table A5, Table A6", ("A2", "A14")),
    Script("gender_spec_robust/gender_spec_robust.py", ("gender_spec_robust.json",), "Table A8", ("A3",)),
    Script("regional_analysis/regional_analysis.py", ("regional_analysis.json",), "Table A10", ("A7",)),
    Script("hetero_trends/hetero_trends.py", ("hetero_trends.json",), "Table A12", ("A8",)),
    # Supplementary analyses ported from the original code; not numbered exhibits.
    Script("gender_analysis/gender_analysis.py", ("gender_analysis.json",), "Supplementary", ("A6",)),
)
