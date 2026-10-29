#! /bin/bash
#
# Process a MP4 file 
# Then add a label and timecode to the video as 720p format
#   
# Usage: 
# 1. Drag the MP4 file to this folder
# 
# Invoke with:
# sh ./TimecodeMP4.sh "Meeting Name" hh:mm:ss

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

# Pick out the MP4 file
cat *.mp4 > Merged.mp4

# Run the ffmpeg command to read the Merged.mp4, add a label and timecode and produce a .mov
#   There are lots of fussy options. See the README.md for details
 
ffmpeg -i Merged.mp4 \
	-s 1280x720 -c:v libx264 -crf 23 -c:a copy \
	-vf "drawtext=text=${label}:               x=100:  y=975: fontsize=48:fontcolor=white: box=1:boxcolor=gray, \
		drawtext=timecode='$start_time': r=30: x=1300: y=975: fontsize=48:fontcolor=white: box=1:boxcolor=gray" \
   	-y \
   	"$outfile"

# # remove the temporary file
rm Merged.mp4

# Play royalty-free beep from https://www.soundjay.com/beep-sounds-1.html to say we're done
afplay ./beep-02.wav

# and distinguish the end of the process in the terminal
echo ""
echo "============ Completed: ${label}"
echo ""

