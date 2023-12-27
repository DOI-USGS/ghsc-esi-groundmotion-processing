#!/bin/bash

for efile in `find . -name event.json`; do
    sed -e 's/"lat":/"latitude":/g; s/"lon":/"longitude":/g; s/"depth":/"depth_km":/g; s/"mag_type":/"magnitude_type":/g' $efile > tmp && mv tmp $efile
done
