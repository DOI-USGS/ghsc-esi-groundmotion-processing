# stdlib imports
import os
from shutil import which
import re
from pathlib import Path

# third party imports
import numpy as np
import pandas as pd
from obspy.geodetics import gps2dist_azimuth
from esi_utils_io.cmd import get_command_output

# local imports
from gmprocess.utils.config import get_config

PREAMBLE = """
\\documentclass[9pt]{extarticle}

% Allows for 9pt article class
\\usepackage{extsizes}

\\usepackage[T1]{fontenc}

\\usepackage{graphicx}
\\usepackage{tikz}

% grffile allows for multiple dots in image file name
\\usepackage{grffile}

% Turn off default page numbers
% \\usepackage{nopageno}

% Needed for table rules
\\usepackage{booktabs}

\\usepackage[english]{babel}

\\usepackage[letterpaper, portrait]{geometry}

\\geometry{
   left=0.75in,
   top=0.0in,
   total={7in,10.5in},
   includeheadfoot
}

\\setlength\\parindent{0pt}

% Use custom headers
\\usepackage{fancyhdr}
\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{0pt}
\\cfoot{\\thepage}
%%\\lfoot{\\today}

\\tikzstyle{box} = [
    draw=blue, fill=blue!20, thick,
    rectangle, rounded corners]

\\begin{document}
"""

POSTAMBLE = """
\\end{document}
"""

STREAMBLOCK = """
\\begin{tikzpicture}[remember picture,overlay]
   \\draw[box] (0, 0.5) rectangle (9, 1.0) node[pos=.5]
       {\\normalsize [EVENT]};
   \\draw[box] (10, 0.5) rectangle (17, 1.0) node[pos=.5]
       {\\normalsize [STATION]};
\\end{tikzpicture}

\\includegraphics[height=0.65\\textheight]
    {[PLOTPATH]}


"""

TITLEBLOCK = """
\\begin{center}

\\vfill

\\large Summary Report

\\vspace{1cm}

gmprocess

\\vspace{1cm}

Code version: [VERSION]

\\vspace{1cm}

\\today

\\vspace{1cm}

\\includegraphics[width=\\textwidth]
    {[MAPPATH]}

[MOVEOUT_PAGE]

\\end{center}

\\vfill

\\newpage\n\n

"""

MOVEOUT_PAGE_TEX = """
\\includegraphics[width=\\textwidth]
    {[MOVEOUTPATH]}
"""


def build_report_latex(
    st_list,
    directory,
    event,
    prefix="",
    config=None,
    gmprocess_version="unknown",
    build_latex=True,
):
    """
    Build latex summary report.

    Args:
        st_list (list):
            List of streams.
        directory (str or pathlib.Path):
            Directory for saving report.
        event (ScalarEvent):
            ScalarEvent object.
        prefix (str):
            String to prepend to report file name.
        config (dict):
            Config dictionary.
        gmprocess_version:
            gmprocess version.
        build_latex (bool):
            Build the report (default is True).
    Returns:
        tuple:
            - Name of pdf or latex report file created.
            - boolean indicating whether PDF creation was successful.

    """
    # Need to get config to know where the plots are located
    if config is None:
        config = get_config()

    # Check if directory exists, and if not, create it.
    directory = Path(directory)
    directory.mkdir(exist_ok=True)

    # Initialize report string with PREAMBLE
    report = PREAMBLE

    # Does the map exist?
    map_file = directory / "stations_map.png"
    if map_file.is_file():
        title_block = TITLEBLOCK.replace("[MAPPATH]", "stations_map.png")

        title_block = title_block.replace("[VERSION]", gmprocess_version)
        moveout_file = directory / "moveout_plot.png"
        if moveout_file.is_file():
            title_block = title_block.replace("[MOVEOUT_PAGE]", MOVEOUT_PAGE_TEX)
            title_block = title_block.replace("[MOVEOUTPATH]", "moveout_plot.png")
        else:
            title_block = title_block.replace("[MOVEOUT_PAGE]", "")
        report += title_block

    # Loop over each StationStream and append it's page to the report
    # do not include more than three.

    # sort list of streams:
    st_list.sort(key=lambda x: x.id)
    event_id = event.id.replace("smi:local/", "")
    event_depth = np.round(event.depth_km, 1)

    epi_dists = []
    for st in st_list:
        streamid = st.get_id()
        tmp_repi = (
            gps2dist_azimuth(
                st[0].stats.coordinates.latitude,
                st[0].stats.coordinates.longitude,
                event.latitude,
                event.longitude,
            )[0]
            / 1000.0
        )
        epi_dists.append(np.round(tmp_repi, 1))

    sort_idx = np.argsort(epi_dists)

    for idx in sort_idx:
        st = st_list[idx]
        streamid = st.get_id()
        repi = epi_dists[idx]

        # Even on windows, latex needs the path to use linux-style forward slashs.
        plot_path = f"plots/{event_id}_{streamid}.png"
        st_block = STREAMBLOCK.replace("[PLOTPATH]", plot_path)
        st_block = st_block.replace(
            "[EVENT]",
            f"{str_for_latex(event_id)} - M{event.magnitude}, "
            f"depth: {event_depth} km",
        )
        st_block = st_block.replace("[STATION]", f"{streamid}, " f"Repi: {repi} km")
        report += st_block

        try:
            prov_latex = get_prov_latex(st)
        except ValueError:
            prov_latex = str_for_latex(
                "Provenance could not be tabulated; this should only happen when the "
                "``any_trace_failures'' option is False because this allows the traces "
                "to have a different number of entries, preventing table construction."
            )

        report += prov_latex
        report += "\n"
        if st[0].has_parameter("signal_split"):
            pick_method = st[0].get_parameter("signal_split")["picker_type"]
            report += f"Pick Method: {str_for_latex(pick_method)}\n\n"
        if "nnet_qa" in st.get_stream_param_keys():
            score_lq = st.get_stream_param("nnet_qa")["score_LQ"]
            score_hq = st.get_stream_param("nnet_qa")["score_HQ"]
            report += f"Neural Network LQ score: {str_for_latex(str(score_lq))}\n\n"
            report += f"Neural Network HQ score: {str_for_latex(str(score_hq))}\n\n"
        if not st.passed:
            for tr in st:
                if not tr.passed:
                    fail_reason = str_for_latex(tr.get_parameter("failure")["reason"])
                    report += f"Failure reason: {fail_reason}\n\n"
                    break
        report += "\\newpage\n\n"

    # Finish the latex file
    report += POSTAMBLE

    res = False
    # Do not save report if running tests
    if "CALLED_FROM_PYTEST" not in os.environ:
        # Set working directory to be the event subdirectory
        current_directory = Path.cwd()
        os.chdir(directory)

        # File name relative to current location
        file_base = f"{prefix}_report_{event_id}"
        tex_name = Path(f"{file_base}.tex")
        pdf_file = Path(f"{file_base}.pdf")

        # File name for printing out later relative base directory
        latex_file = directory / tex_name
        with open(tex_name, "w", encoding="utf-8") as f:
            f.write(report)

        # Can we find pdflatex?
        try:
            pdflatex_bin = which("pdflatex")
            if os.name == "nt":
                # seems that windows needs two dashes for the program options
                flag = "--"
            else:
                flag = "-"
            pdflatex_options = f"{flag}interaction=nonstopmode {flag}halt-on-error"
            cmd = f"{pdflatex_bin} {pdflatex_options} {tex_name}"
            if build_latex:
                res, stdout, stderr = get_command_output(cmd)
                report_file = latex_file
                if res:
                    if pdf_file.is_file():
                        report_file = str(pdf_file)
                        auxfiles = directory.glob(f"{file_base}*")
                        for auxfile in auxfiles:
                            if str(pdf_file) not in str(auxfile):
                                auxfile.unlink(missing_ok=True)
                    else:
                        res = False
                else:
                    res = False
            else:
                print("pdflatex output:")
                print(stdout.decode())
                print(stderr.decode())
        except BaseException:
            report_file = ""
        finally:
            os.chdir(current_directory)
    else:
        report_file = "not run"

    # make report file an absolute path
    report_file = directory / report_file

    return (report_file, res)


def get_prov_latex(st):
    """
    Construct a latex representation of a trace's provenance.

    Args:
        st (StationStream):
            StationStream of data.

    Returns:
        str: Latex tabular representation of provenance.
    """
    # start by sorting the channel names
    channels = [tr.stats.channel for tr in st]
    channelidx = np.argsort(channels).tolist()

    trace1 = st[channelidx.index(0)]
    prov1 = trace1.provenance.get_prov_dataframe().to_dict()
    prov_ind = [v for v in prov1["Index"].values()]

    final_dict = {
        "Process Step": [v for v in prov1["Process Step"].values()],
        "Process Attribute": [v for v in prov1["Process Attribute"].values()],
        f"{trace1.stats.channel} Value": [v for v in prov1["Process Value"].values()],
    }

    for i in channelidx[1:]:
        trace2 = st[i]
        prov2 = trace2.provenance.get_prov_dataframe().to_dict()
        final_dict[f"{trace2.stats.channel} Value"] = [
            v for v in prov2["Process Value"].values()
        ]

    last_row = -1
    for i, row in enumerate(prov_ind):
        if row == last_row:
            final_dict["Process Step"][i] = ""
            continue
        last_row = row

    newdf = pd.DataFrame(final_dict)
    # prov_string = newdf.to_latex(index=False)
    if hasattr(newdf, "map") and callable(newdf.map):  # applymap ->map in Pandas 2.1.0
        newdf = newdf.map(str_for_latex)
    else:
        newdf = newdf.applymap(str_for_latex)
    prov_string = newdf.style.to_latex(hrules=True)
    # Annoying hack because pandas removed the functionality to hide the index when
    # writing to latex.
    prov_string = prov_string.replace("{llll", "{lll")
    prov_string = re.sub(r"\n\d* &", "\n", prov_string)

    prov_string = "\\tiny\n" + prov_string
    return prov_string


def str_for_latex(string):
    """
    Helper method to convert some strings that are problematic for latex.
    """
    string = string.replace("_", "\\_")
    string = string.replace("$", "\\$")
    string = string.replace("&", "\\&")
    string = string.replace("%", "\\%")
    string = string.replace("#", "\\#")
    string = string.replace("}", "\\}")
    string = string.replace("{", "\\{")
    string = string.replace("~", "\\textasciitilde ")
    string = string.replace("^", "\\textasciicircum ")
    return string
