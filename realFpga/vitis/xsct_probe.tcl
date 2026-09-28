puts "XSCT_PROBE_BEGIN"
puts "TCL_VERSION=[info patchlevel]"
puts "XSCT_VERSION_BEGIN"
version
puts "XSCT_VERSION_END"
puts "PLATFORM_HELP_BEGIN"
help platform
puts "PLATFORM_HELP_END"
puts "APP_HELP_BEGIN"
help app
puts "APP_HELP_END"
puts "BSP_HELP_BEGIN"
help bsp
puts "BSP_HELP_END"
puts "REPO_APPS_BEGIN"
repo -apps
puts "REPO_APPS_END"
puts "XSCT_PROBE_END"
exit
