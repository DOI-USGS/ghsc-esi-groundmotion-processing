## main


## 2.1.2 / 2024-11-14
- Enhancements
  - Station distance (epicentral distance) added to the reports
  - Add support velocity and dispacement COSMOS and DMG files
  - More graceful exiting when bad eventid is inputted to `download`
  - Allow `reports` to continue processing when an event directory is empty (no data)
  - Update default config to use the Ramos-Sepulveda et al. (2023) high-pass corner selection method, and increase the p-wave shift to -2 sec from -1 sec. 
- Bug fixes
  - Resolve ps2ff imports
  - Distance to source in reports fixed for failed traces
- Dependencies
  - Remove cap on scipy version, and resolve deprecated functions that were removed in v1.14.
- Other
  - Exclude 'XO' network as default in config ('XO' is an assortment of temporary deployment networks in the Alaska region)
  - Added a fetch_orfeus script to bin that allows users to create gmprocess-compliant workspace files
    from data downloaded from the European ORFEUS Engineering Strong Motion (ESM) web-service.
  - Removed what looked to be a workaround to capture MassDownloader output sent to stdout and redirect to our logging. 
    With the newer versions of Obspy this is no longer necessary.

## 2.1.1 / 2024-09-16
- Enhancements
  - Modified default frequencies for FAS metrics to be consistent with (Kottke AR, et al, 2021) 
  - Added FAS check to unit test for `export_metric_tables`
- Bug fixes
  - Fixed bug when running `compute_station_metrics` so that failed streams are not added to the workspace
  - Fixed mismatch in stream workspace `add_rupture` call definition and it's use in assemble
  - Fix bug in FAS not being exported correctly when running `mtables`
  - Fixed missing vertical/horizontal orientation information in KNET reader.

## 2.1.0 / 2024-06-09
- New features
  - Add UCLA review GUI
  - Add --conf and --data command line arguments for the gmrecords command.
- Enhancements
  - Remove sansmathfonts latex package since it is not necessary and can create latex dependency issues on some systems.
  - Speed up station metric calculations by removing unnecessary repeated calculations.
  - Updated line styles of annotation lines in SNR plots.
  - Remove the `export_shakemap` subcommand.
  - Default config updates
    - Change KO smoothing paramter to 188.5.
    - Add arias intensity.
    - Lower pga threshold on distance search criteria.
    - Update release instructions in CONTRIBUTING.md.
- Bug fixes
  - Resolve failing unit test related to obspy bugfix (https://github.com/obspy/obspy/pull/3422)
  - Fix bug in setting event id as a comma separated list with the "-e" argument.
  - Fix `autoshakemap` to use `export_gmpacket` subcommand instead of `export_shakemap`.

## 2.0.0 / 2024-02-26
- Documentation Updates
  - Switched over to the vectorized openquake for the mixed effects tutorial.
  - Fixed typos and removed unused imports for openquake
  - Removed admonition from install.md that resulted in an error (but didn't break the pipeline)
- Code improvements
  - Refactored the code for computing metrics.
  - Reorganize downloading event information (event, rupture geometry, STREC results) and loading it into the workspace. All information is downloaded in the `download` subcommand, and loaded into the workspace with the `assemble` subcommand. Subsequent commands all load the event information from the workspace.
  - Use full words for keys in `event.json` files (magnitude, magnitude_type, longitude, latitude, depth_km).
  - Handle the dateline discontinuity in fdsn_fetcher.
  - Modified the taper applied in the frequency domain when resampling for high-frequency response spectra; this narrows the taper so that it doesn't affect the amplitude as much.
- Config changes
  - Changed format for specifying response spectral periods.
  - Changed default integration method to frequency domain.
  - Make the integration config options consistent with the trace.integrate function arguments.
- Other
  - Turned off automatic generation of moveout plot since it isn't getting used.
  - Renamed src/gmprocess/utils/test_utils.py to src/gmprocess/utils/test_utils.py to avoid it being detected as a unit test module.
  - Decrease precision in fetcher bounds and fix Geonet bounds to include negaive longitudes.
  - Move the "config" subcommand to be a stand-alone command line program called "gmprocess_config".
  - Removed "list_metrics" command.
  - Removed cap on python version, increased minimum version to 3.9
  - Updated cwb_gather command, and renamed to cwa_gather and updated instructions to include TSMIP and StationXML now that it is available. 
  - Capped scipy version to be less than 1.13 because of incompatibility with obspy (should be fixed in next version of obspy).

## 1.3.2 / 2024-02-03
- Fix bug in trace units that was created in 1.3.1 and affects all velocity instruments.

## 1.3.1 / 2024-01-31
- Fix bug that vs30measured should be bool, not float.
- Adjust io tests to make use of pytest fixtures and get a bit of speedup.
- Re-organize waveform_processing/instrument_response.py module.
- Add trace.warning method.
- Add trace warning when computed and reported sensitivities differ (captured from obspy).
- Lower default PGA threshold in search_parameters to 0.001 g.
- Created a module/class for handling provenance (core.provenance.Provenance), and added provenance entries for person/software and removed these entries from the Trace provenance.

## 1.3.0 / 2023-11-18

- Add unprocessed waveform to summary plots.
- Add config option to enable/disable STREC.
- Add method to retrieve rupture model geometry info from workspace.
- Add clipping probability as a trace processing parameter; remove it from failure message.
- Change default config to specify providers.
- Move STREC download to occur in "download" subcommand; results are stored in "strec_results.json" in event directory.
- Add optional search parameters to be based on magnitude for duration and PGA threshold for distance.
- Restrict NCEDC provider bounds.
- Remove unnecessary hasbangs and `__name__ == "__main__"` blocks.
- Documentation
  - Add STREC configuration to initial setup instructions
  - Add search_parameters parameters to config section of the manual.
- Bugfixes
  - Fix false negatives in clipping algorithm that arise due to long pre-event noise; this is fixed by trimming only the low amplitude tail of the record rather than a static window duration.
  - Add STREC configuration to .gitlab-ci.yml
  - Add missing DIMENSION_UNITS in constants module.
  - Fix bug in event depth.
  - Fix bug that prevented metric tables from exporting when colocation is turned off.
  - Avoid bug in FAS output to gmpacket.
  - Modify fetcher imports to avoid errors resulting from .DS_store or similar files.
  - Always include clipping probability as a trace processing parameter.

## 1.2.9 / 2023-10-19

- Added station metric units to constants.
- Bugfixes
  - Resolve key error that was preventing writing of metric tables when Arias Intensity was requested. 
  - Resolve bug that occurs when multiple channels/stations are present in the invetory when trying to retrieve the sampling rate for the metric table.

## 1.2.8 / 2023-08-21

- Change resample method to use default Hanning window (was not using a window previously).
- Define new Metrics class to improving handling of intensity metrics.
- Define new MetricsXML class to isolate the conversion of metrics into an XML.
- Define new Rupture class which adds rupture model information to workspace file.
- Refactor StationSummary into multiple separate classes:
  - WaveformMetric, WaveformMetricList, WaveformMetricCollection, WaveformMetricsXML
  - StationMetric, StationMetricCollection
- Pulled out flatfile stuff from StreamWorkspace into a Flatfile class, and put ASDF path stuff into path_utils.py.
- Refactor summary plot code.
- Optimize getTables method.
- Temporarily remove response spectra tutorial
- Bugfixes
  - Update BeautifulSoup4 min version to be 4.11.0
  - Knet reader wasn't getting the project config file.
  - Fix documentation rendering issues introduced by recent refactoring.
  - Configuration option for CESMD fetcher earthquake time window was not being parsed.

## 1.2.7 / 2023-04-28

- Add the "no_noise" option to the "windows" section of the config to allow for processing older waveforms that did not include pre-event noise. 
- Update workspace so that when the config attribute is set, any missing values entries are filled in with defaults.
- Moved supplemental stream info out of StationXML description field and into auxiliary data.
- Added a "fix_inventory" utility script to move data supplemental stream data from StationXML to auxiliary data in existing workspace files.
- Bugfixes
  - Avoid gmpacket export error when no records are present.
- Adding support for STREC (https://code.usgs.gov/ghsc/esi/strec#table-of-contents) in gmprocess- 
   probabilities of different regimes and supporting STREC information are now added to the auxiliary 
   data section of the workspace.

## 1.2.6 / 2023-03-18

- Update URL in download code.
- Bugfixes
  - Config wasn't being passed to COSMOS reader, or to StreamArray.
  - Fix units in ground motion packet output.

## 1.2.5 / 2023-03-17

- Updated obspy data reader to allow station XML base names to match corresponding miniseed file names.
- Added support for passing in a config directory to `gmrecords config-u`
- Add support for bounds in FDSN providers.
- Added bandpass and bandstop filter types for StationTrace. Improved modularity of low/high pass filter code.
- Added unit tests for the StationTrace filter types.
- Added event depth to gmprocess reports
- Updated pphase_test to use StationTrace object instead of obspy trace
- Allowed string for label parameter in getStreams() method
- Added warning if label not found in workspace file when using getStreams() method 
- Bugfixes
  - Fixed bug in station_summary.py that was using deprecated _quadrilaterals property of EdgeRupture class.
  - Fixed bug in StationTrace filters where the bandpass option was not implemented and no warning was given.
  - Fixed bug in fdsn_fetcher.py that caused either URL or name-based data providers to fail on download
  - Allow more date formats for time stamps in Engineering Strong Motion (ESM) ASCII reader.
  - Adjust test configuration to allow test-specific config files to be used without sometimes being overwritten

## 1.2.4 / 2023-02-09

- Add config option to send email on errors.
- Handle unexpected exception zip checking in `assemble` subcommand
- Limit histogram clipping algorithm to 100 largest peaks and stop algorithm once we find one clipping region (positive and negative).
- Improved email alert error message.
- Removed unnecessary loops from corner frequency method.
- Bugfixes
  - Use event depth in km, not m, in hypocentral and rupture distance calculations. Bug was introduced in v1.2.3.
  - Account for pre-event noise duration, event noise duration, and shaking duration in signal-to-noise calculation. Plot normalized spectra in report.
  - Raise exceptions that were trapped for but not raised by the addition of the email alert notifications. 
- Added command to create [ground motion packet](https://github.com/SCEDC/ground-motion-packet/#description-of-gmp-a-geojson-specification-for-ground-motion-metrics) files.
- Alter how TEST_DATA_DIR is constructed in constanst.py to facilitate running local tests with PyTest against a Conda-Forge or PyPi installed gmprocess distribution 
- Updated reader for the Engineering Strong Motion (ESM) ascii format.

## 1.2.3 / 2022-12-23

- Add MANIFEST.in and removed some unused files.
- Add support to specify specific FDSN providers and URLs in config file.
- Improve documentation of config file.
- Modified the signal-to-noise-ratio calculation to normalize the spectra by duration.
- Bugfix for how period arrays are defined when using start/stop values in the config file along with the logspace option.

## 1.2.2 / 2022-11-08

- Adding "Merge Request Guidelines" and "Release Steps" sections to developer resources. 
- Improve projects subcommand.
- Always prompt for names of 'data' and 'conf' directories with reasonable defaults.
- Provide appropriate error message when attempting to list, switch, or delete projects when none exist.
- Allow use of projects subcommand from Python scripts.
- Fixes SAC format units conversion issue. 
- Add lp_max option for lowpass_max_frequency method.
- Add the `autoprocess` subcommand, which requires moving some subcommand arguments to gmprocess; this includes `eventid`, `textfile`, `label`, `num-processes`, and `overwrite`.
- Note that moving the `label` argument to gmrecords from the subcommands means that the short flag `-l` conflicts with `log` so the short flag for log has been removed.
- Include "passed" or "failed" for each station in export_failure_tables in addition to failure reason.
- Moved location of the changelog (this file) from doc_source/contents/developer/changelog.md to CHANGELOG.md.
- Bugfix in `assemble` where the project conf file was not getting used while constructing the StreamCollection/StreamArray. 

## 1.2.1 / 2022-10-04

- Data fetcher bugfix.
- Improvement to Windows install instructions.
- Add changelog.
- Add "config" subcommand to gmrecords.
- Fix pandas to_latex warning.
- Add check_stream config section with any_trace_failures key. 
- Modify StationID column in metric tables to include full channel code when available. 
- Move C code to esi-core repository.
- Added rename project flag for gmrecords proj subcommand
- Switched from os.path to Pathlib in projects.py and gmrecords.py

## 1.2.0 / 2022-08-15

- First release with wheels uploaded to pypi.
- Major reorganization of code, putting the base package inside src/. 
- Replace dask with concurrent.futures
- Factor out pkg_resources
- Remove support for Vs30 (because it adds too many dependencies)
- Fix code version method and add DATA_DIR to constants
- Changed setup to use pyproject.toml and setup.cfg; still need setup.py but only for cython stuff.
- Factor out use of libcomcat.
- Added "magnitude" and "none" options for the method argument to signal_end function.
- Make processing steps auto detected via decorators.
- Reorganize processing step modules.
- Resolve a lot of future warnings.
- In config, replace "do_check" with "enabled" for a more consistent naming convention across config sections.
- Reorganiztaion of config structure to allow for parameters to be unspecified and thus use the default values from the associated methods. 
- More gracefully handle cases where workspace file does not exist but is expected.
- Add label arg to gmconvert.
- Make colocated selection optional.
- Replace stastic map with interactive HTML map and add to CLI tutorial in documentation.
- Remove cartopy dependency.
- Get scnl from COSMOS comments.
- Add freq differentiation option.
- Ignore lowpass_max_frequency step if manually set.
- Add support for UCLA manually selected lowpass corners
- Update CEUS network in COSMOS Table 4
- Reorganize FDSN config options to better match the respective obspy functions.
- Add support for frequency domain filtering.
- Add support for frequency domain integration.
- Turn off logging to stream if using log file and allow user specified filename for logging.
- Apply min freq criteria to high pass filter. 
- Fix confusion between 'unit_types' and 'units'.
- Adding in code to handle Taiwan data script.
- Added cosmos writer.
- Remove legacy "gmsetup" command.
- Reduced redundancy in the first three steps of MetricsController.execute_steps.
- Allow for magnitude-distance-based channel prefrence order.
- Added config to ASDF and read it from there rather than file system if it exists.
- Replaced pyyaml with ruamel.yaml because the latter is actively maintained and allows persistent comments.
- Store noise time series in output ASDF file.

## 1.1.10 / 2021-09-21

- Add ANN clipping code and test.

## 1.1.9 / 2021-09-20

- Fix ExponentialSmoothing future warning
- Remove legacy "gmprocess2" command.
- Relax dependency versions.
- Fix jerk unit tests.

## 1.1.8 / 2021-07-19

- Added the auto_shakemap subcommand
- Bugfix to CESMD fetcher
- Improved handling of nans and empty data structures
- Simplified error logging
- Added "sorted duration" metric
- Changed unknown network to '/' rather than 'ZZ'
- Added event id to output filenames where appropraite
- Improved efficiency by removing calls to trace.times()
- Optimized distance calculations
- Fix behavior when no project has been configured
- Added a linear mixed effects tutorial to the docs
- Removed unnecessary processing steps that we occurring in the download subcommand
- Added a method for finding USGS event id from other projects and included a table for cross referencing event IDs.
- Changed location of temp directory used for reading in data.

## 1.1.7 / 2020-12-20

- More updates to try to support Windows OS and build with conda.

## 1.1.6 / 2020-12-17

- More updates to try to support Windows OS.

## 1.1.3 / 2020-12-11

- Fixed precision of SA strings in shakemap output json.
- Add Windows install script and some refactoring to try to support Windows OS.
- Renamed io/fdsn to io/obspy.

## 1.1.2 / 2020-08-31

- Fixes to c compiler issues.

## 1.1.0 / 2020-08-30

- Instrument response correction will now always try to use poles/zeros to remove 
  response, and only use the simpler sensitivity method if no poles/zeros are available.
- The pattern matching on excluding FDSN records is improved to better handle wildcards, 
  and can be applied to channel, network, station, and location codes.
- Fixed a bug where zeros could be returned by the Konno-Omachi smoothing algorithm. 
  Now it will return nans if there's no point within the smoothing window, and there's 
  an option to zero-pad the data to ensure that there are points in all windows.
- Fixed bug in Raoof et al. attention model (that is used for fitting a Brune spectra 
  to the signal spectra)
- Added a goodness-of-fit measure of the Brune spectra to the signal spectra.
- Fixed bug in station map that allowed the extent to be too small if there's only one 
  station and it is very close to the earthquake.
- Fixed bugs in code for reading the workspace file into Matlab that arose because it 
  was not kept up to date with other changes in the code.
- Relaxed the restrictions placed on the allowed IMT/IMC combinations.
- Fixed a bug in how the upsampling was done when computing high-frequency response 
  spectra. The code now does the full upsampling method as recommended by Boore and 
  Goulet (2014; DOI 10.1007/s10518-013-9574-9), and we added a test of low sample rate 
  records against the high-frequency response spectra reported by NGA East for the same 
  record.

## 1.0.4 / 2020-03-25

- Fix handling sensitivity units other than meters.
- Added optional p_arrival_shift parameter to allow users to shift signal split time
  left or right as needed.
- General optimization.

## 1.0.3 / 2020-01-13

- Minor config tweaks.
- Modified Turkey/KNET fetchers to handle cases where no earthquakes are found.
- Exit gracefully when no data is found.
- Added Geonet near real-time url to list of FDSN services when event is less than 7 
  days old.
- Added CESMD fetcher. 
- Added matlab functions for reading ASDF and documentation.
- Allow for setting the precision of data tables.

## 1.0.2 / 2019-10-17

- Now using ASDF dataset ifilter() method to speed up search times for waveforms in 
  HDF files.
- Improved windowing to remove signal from multiple events in the same waveform.
- Added moveout plots to summary report.
- Improved spectral fitting.
- Add QA checks for multiple events.

## 1.0.1 / 2019-09-30

- Adding reader/tests for Chilean (Renadic network) format.
- Documentation fixes.

## 1.0.0 / 2019-09-25

- Initial release.
