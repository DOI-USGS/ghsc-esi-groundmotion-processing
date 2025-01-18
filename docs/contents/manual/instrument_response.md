# Instrument Response

By default, gmprocess is configured to include accelerometers (instrument code "N") and high gain seismometers (instrument code "H").
Because the instrument response for accelerometers is flat down to zero frequency, it is typically acceptable to simply apply the sensitivity correction to convert from counts to physical units.
The processing step to remove the instrument response in gmprocess includes some logic for quality control of the metadata and to determine whether to apply the full instrument deconvolution or the sensitivity correction. 

[StationXML](https://www.fdsn.org/xml/station/) files report the total sensitivity of the instrument as well as the gains associated with each stage of the instrument response.
The units of the total sensitivity and each stage are also reported.
Based on this information, we apply a few quality control checks:
- Are the total and instrument sensitivities consistent with each other?
- Are the units that result from combining all of the stages consistent with the instrument type (accelerometer versus seismometer)?
- Are the units of the total sensitivity consistent with the instrument type?

Based on this information, we developed a flowchart below to determine if we should apply the full instrument response correction, remove the overall sensitivity, or reject/fail the record. 
This represents a compromise between requiring perfect metadata and allowing for some inconsistencies, which we expect will not result in problematic data.
For example, if the units that result from the reported instrument response stages are inconsistent with the instrument type, but the instrument is an accelerometer, and the total sensitivity units are correct, then we remove the sensitivity and assume that the mistake in the stages is inconsequential.
However, if the instrument is a seismometer, we cannot simply apply the sensitivity correction, so we reject the record.

```{figure} ../../_static/instrument_response_diagram.png
Instrument response flowchart.
```
