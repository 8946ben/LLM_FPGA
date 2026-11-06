    class axi_latency_control extends axi_latency;
        rand int    wctrl_latency;
        rand int    wdata_latency;
        rand int    wbrsp_latency;
        rand int    rctrl_latency;
        rand int    rdata_latency;
        `uvm_object_utils_begin(axi_latency_control)
        `uvm_object_utils_end
        function new ( string name = "axi_latency_control" );
            super.new(name);
        endfunction
        virtual function int get_wctrl_lat();
            int delay;
            void'(std::randomize(delay) with {
				delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};
				delay inside {[0:256]};
				});
            wctrl_latency = delay;
            return wctrl_latency;
        endfunction
        virtual function int get_wdata_lat();
            int delay;
            void'(std::randomize(delay) with {
				delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};
				delay inside {[0:256]};
				});
            wdata_latency = delay;
            return wdata_latency;
        endfunction
        virtual function int get_wbrsp_lat();
            int delay;
            void'(std::randomize(delay) with {
				delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};
				delay inside {[0:256]};
				});
            wbrsp_latency = delay;
            return wbrsp_latency;
        endfunction
        virtual function int get_rctrl_lat();
            int delay;
            void'(std::randomize(delay) with {
				delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};
				delay inside {[0:256]};
				});
            rctrl_latency = delay;
            return rctrl_latency;
        endfunction
        virtual function int get_rdata_lat();
            int delay;
            void'(std::randomize(delay) with {
				delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};
				delay inside {[0:256]};
				});
            rdata_latency = delay;
            return rdata_latency;
        endfunction
    endclass
