# Offline export from an isolated copy of the qualified HLS synthesis.
open_project hls
open_solution solution1
export_design -format ip_catalog -vendor user.org -library hls -version 4.1
close_project
puts "M14_D64_PRIVATE_EXPORT=PASS"
exit
