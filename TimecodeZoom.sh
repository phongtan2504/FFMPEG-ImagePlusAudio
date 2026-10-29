#! /bin/bash
#
# Add a label and timecode to a Zoom recording, then
# output the video as 720p format
#   
# Usage: 
# 1. Drag the Zoom (.mp4) file from the SD card to this folder
# 
# Invoke with:
# sh ./TimecodeZoom.sh "Meeting Name" hh:mm:ss

# get_mp4_dimension() - retrieve the named dimension from the named file
# params are filename, dimensionName (kMDItemPixelHeight, kMDItemPlxelWidth)

# example usage:
# height=$(get_mp4_dimension "your-video.mp4" kMDItemPixelHeight) || exit 1
# echo "Video height is ${height}px"

get_mp4_dimension() {
  local file="$1"
  # ensure the file exists
  [[ -f "$file" ]] || { echo "Error: '$file' not found" >&2; return 1; }

  # pull the raw metadata and extract digits
  mdls -name "$2" -raw "$file" \
    | grep -Eo '^[0-9]+' \
    || { echo "Error: no height metadata" >&2; return 1; }
}

# Get the label text
label="$1"

# Extract hours, minutes, and seconds from the time stamp passed in
IFS=: read -r hours minutes seconds <<< "$2"

# Tweak the entered time to add ";00" 
start_time="$hours\:$minutes\:$seconds\;00"

# Debug label and start time
# echo "***** $label" "$start_time"

# infile is the (first) .mp4 file
mp4_files=( *.mp4 )
infile="${mp4_files[0]}"

# Append  "-timecoded.mp4" to the provided label for the file name
outfile="${label}-timecoded.mp4"

# Get dimensions, compute the location of the labels

vh=$(get_mp4_dimension "$infile" "kMDItemPixelHeight")
vw=$(get_mp4_dimension "$infile" "kMDItemPixelWidth")
lposx=100
lposy=$(( vh * 95 / 100 ))
tposx=$((vw / 2 + 100))
tposy="$lposy"

# echo "============"
# echo "$infile", $vh, $vw, "$lposx", "$lposy", "$tposx", "$tposy"

# Run the ffmpeg command to read the Zoom .mp4 recording, add a label and timecode and produce a .mov
#   There are lots of fussy options. See the README.md for details
 
ffmpeg -i "$infile" \
	-s 1280x720 -c:v libx264 -crf 23 -c:a copy \
	-vf "drawtext=text=${label}:               x=$lposx:  y=$lposy: fontsize=18:fontcolor=white: box=1:boxcolor=gray, \
		drawtext=timecode='$start_time': r=30: x=$tposx:  y=$tposy: fontsize=18:fontcolor=white: box=1:boxcolor=gray" \
   	-y \
   	"$outfile"

# Play royalty-free beep from https://www.soundjay.com/beep-sounds-1.html to say we're done
afplay ./beep-02.wav

# and distinguish the end of the process in the terminal
echo ""
echo "============ Completed: ${label}"
echo ""
