# Introduction
This is a project designed to provide a number of functions related to parsing and processing earthquake ground motion data, building on top of the [ObsPy](https://github.com/obspy/obspy/wiki) library.
Most of the extensions that we provide are to handle strong motion data and related issues.


# Documentation
- Please note, we are in the process of improving the documentation and that there are some incomplete sections.
- The full documentation can be viewed locally by running the `docs/makedocs.sh` script.
- The documentation is also available [here](https://ghsc.code-pages.usgs.gov/esi/groundmotion-processing/).
- The MATLAB functions included in the `tools/matlab` directory include a short [tutorial](tools/matlab/readme.md)

# Getting Help
The developers can be reached at [gmprocess@usgs.gov](mailto:gmprocess@usgs.gov).

If you would like to post an issue to ask a question, request a new feature, or report a bug, you can do so at the [github mirror](https://github.com/DOI-USGS/ghsc-esi-groundmotion-processing) of this repository. 

If you would like to contribute merge requests to this repository, please let us know and we can add you as a collaborator. 
This will require that you create an account at code.usgs.gov, which is a more involved process than creating a personal account at gitub.com and posting to the issues on the github mirror.

# Suggested Citation
If you wish to cite this software please cite:

- Thompson, E.M., M. Hearne, B.T. Aagaard, J.M. Rekoske, C.B. Worden, M.P. Moschetti, H.E. Hunsinger, G.C. Ferragut, G.A. Parker, J.A. Smith, K.K. Smith, and A.R. Kottke (2024). USGS Automated Ground Motion Processing Software Version 2, U.S. Geological Survey software release, doi: [10.5066/P13HMKFJ](https://doi.org/10.5066/P13HMKFJ).

- Thompson, E.M., M. Hearne, B.T. Aagaard, J.M. Rekoske, C.B. Worden, M.P. Moschetti, H.E. Hunsinger, G.C. Ferragut, G.A. Parker, J.A. Smith, Smith, K.K., and A.R. Kottke (2025). Automated, Near Real‐Time Ground‐Motion Processing at the US Geological Survey. _Seismological Research Letters_, 96(1), pp.538-553, doi: [10.1785/0220240021](https://doi.org/10.1785/0220240021).

# Journal Articles
The list below is a subset of articles that made use of this software in their study. If you would like to have an article added to this list, please open an issue or email the developers.

- Ahdi, S.K., B.T. Aagaard, M.P. Moschetti, G.A. Parker, O.S. Boyd, and W.J. Stephenson (2024). Empirical ground-motion basin response in the California Great Valley, Reno, Nevada, and Portland, Oregon. _Earthquake Spectra_, 40(2): 1099-1131, doi: [10.1177/87552930241237250](https://doi.org/10.1177/87552930241237250).

- Boyd OS, D. Churchwell, M.P. Moschetti, et al. (2024). Sediment thickness map of United States Atlantic and Gulf Coastal Plain Strata, and their influence on earthquake ground motions. _Earthquake Spectra_, 40(1): 89-112, doi: [10.1177/87552930231204880](https://doi.org/10.1177/87552930231204880).

- Chatterjee, A., D.T. Trugman, G. Hirth, J. Lee, and V.C. Tsai (2024). High‐frequency ground motions of earthquakes correlate with fault network complexity. _Geophysical Research Letters_, 51(12), doi: [10.1029/2024GL109418](https://doi.org/10.1029/2024GL109418).

- Hirakawa, E., G.A. Parker, A. Baltay, and T. Hanks (2023). Rupture directivity of the 25 October 2022 Mw 5.1 Alum Rock earthquake. _The Seismic Record_, 3(2): 144-155, doi: [10.1785/0320230013](https://doi.org/10.1785/0320230013).

- Ji, C., A. Cabas, A. Kottke, M. Pilz, J. Macedo, and C. Liu (2023). A DesignSafe earthquake ground motion database for California and surrounding regions. _Earthquake Spectra_, 39(1): 702–721, doi: [10.1177/87552930221141108](https://doi.org/10.1177/87552930221141108).

- Li, M., E.M. Rathje, J.P. Stewart, M.E. Ramos-Sepulveda, and Y.M. Hashash (2025). Regional adjustment to the NGA-East GMM for Texas, Oklahoma, and Kansas. _Earthquake Spectra_, doi: [10.1177/87552930251313817](https://doi.org/10.1177/87552930251313817).

- Mohammed, S., R. Shams, C.C. Nweke, T.E. Buckreis, M.D. Kohler, Y. Bozorgnia, and J.P. Stewart (2024). Usability of Community Seismic Network recordings for ground-motion modeling. _Earthquake Spectra_, 40(4): 2598-2622, doi: [10.1177/87552930241267749](https://doi.org/10.1177/87552930241267749).

- Moschetti M.P., E.M. Thompson, J.M. Rekoske, M. Hearne, P. Powers, D. McNamara, and C. Tape (2019). Ground‐Motion Amplification in Cook Inlet Region, Alaska, from Intermediate‐Depth Earthquakes, Including the 2018  7.1 Anchorage Earthquake. _Seismological Research Letters_, 91(1): 142–152, doi: [10.1785/0220190179](https://doi.org/10.1785/0220190179).

- Moschetti, M.P., B.T. Aagaard, S.K. Ahdi, J. Altekruse, O.S. Boyd, A.D. Frankel, J. Herrick, M.D. Petersen, P.M. Powers, S. Rezaeian, and A.M. Shumway (2024). The 2023 US national seismic hazard model: Ground-motion characterization for the conterminous United States. _Earthquake Spectra_, 40(2): 1158-1190, doi: [10.1177/87552930231223995](https://doi.org/10.1177/87552930231223995).

- Parker, G.A., and A.S. Baltay (2022). Empirical Map‐Based Nonergodic Models of Site Response in the Greater Los Angeles Area. _Bulletin of the Seismological Society of America_, 112(3): 1607–1629, doi: [10.1785/0120210175](https://doi.org/10.1785/0120210175)

- Rekoske J.M., E.M. Thompson, M.P. Moschetti, M. Hearne, B.T. Aagaard, and G.A. Parker (2020). The 2019 Ridgecrest, California, Earthquake Sequence Ground Motions: Processed Records and Derived Intensity Metrics. _Seismological Research Letters_, 91(4): 2010–2023, doi: [10.1785/0220190292](https://doi.org/10.1785/0220190292)

# Disclaimer

Any use of trade, firm, or product names is for descriptive purposes only and does not imply endorsement by the U.S. Government.
