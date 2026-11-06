foreach command {rst jtag} {
    puts "M14_HELP=$command"
    puts [help $command]
}
exit 0
