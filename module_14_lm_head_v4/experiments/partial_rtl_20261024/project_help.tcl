puts "FILE_COMMANDS=[info commands *file*]"
puts "REMOVE_COMMANDS=[info commands *remove*]"
puts "DELETE_COMMANDS=[info commands *delete*]"
if {[llength [info commands delete_file]]} {help delete_file}
if {[llength [info commands delete_files]]} {help delete_files}
if {[llength [info commands remove_files]]} {help remove_files}
exit
