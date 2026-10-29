#! /bin/bash
#
# Process a folder of MP_ROOT files from a Sony Handycam
# Then add a label and timecode to the video as 720p format
#   
# Usage: 
# 1. Drag the MP_ROOT directory to this folder
# 
# Invoke with:
# sh ./TimecodeMP_ROOT.sh "Meeting Name" hh:mm:ss

# Get the label text
label="$1"

# Extract hours, minutes, and seconds
IFS=: read -r hours minutes seconds <<< "$2"

# Tweak the entered time to add ";00" 
start_time="$hours\:$minutes\:$seconds\;00"

# Debug label and start time
# echo "***** $label" "$start_time"

# Append  "-timecoded.mp4" to the provided label for the file name
outfile="${label}-timecoded.mp4"

# Concatenate all the .MPG files in the MP_ROOT folder
cat MP_ROOT*/101PNV01/*.MPG  > Merged.MPG

# Run the ffmpeg command to read the named files, add a label and timecode and produce a .mov
#   There are lots of fussy options. See the README.md for details
ffmpeg -i Merged.MPG \
	-s 1280x720 -c:v libx264 -crf 23 -c:a copy \
	-vf "drawtext=text=${label}:              x=30: y=440: fontsize=24:fontcolor=white: box=1:boxcolor=gray, \
		drawtext=timecode='$start_time': r=30: x=550: y=440: fontsize=24:fontcolor=white: box=1:boxcolor=gray" \
   	-y \
   	"$outfile"

# remove the temporary file
rm Merged.MPG

# Play royalty-free beep from https://www.soundjay.com/beep-sounds-1.html to say we're done
afplay ./beep-02.wav

# and distinguish the end of the process in the terminal
echo ""
echo "============ Completed: ${label}"
echo ""

