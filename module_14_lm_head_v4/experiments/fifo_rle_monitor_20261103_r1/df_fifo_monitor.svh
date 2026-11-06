`ifndef DF_FIFO_MONITOR__SV
    `define DF_FIFO_MONITOR__SV
    class df_fifo_monitor extends sample_agent;
        virtual df_fifo_intf in_intf;
        logic [31:0] rt_depth;
        logic [31:0] rt_depth_arr[$];
        logic [1:0] rt_block_arr[$];
        logic chan_status_wb;
        logic chan_status_rb;
        logic [31:0] total_run_time;
        logic [31:0] total_wb_time;
        logic [31:0] total_rb_time;
        logic [31:0] max_used_depth;
        dump_file_agent chan_file;
        integer depth_fd,block_fd;
        longint unsigned depth_run,block_run,depth_samples,block_samples,pushes,pops,clamped_reads;
        logic[31:0] depth_last;
        logic[1:0] block_last;
        bit rle_closed;

    function new(dump_file_agent file_inst, virtual df_fifo_intf intf_inst, dump_file_agent chan_file_inst);
        super.new(file_inst);
        this.in_intf = intf_inst;
        this.chan_file = chan_file_inst;
        this.rt_depth = 32'h0;
        this.chan_status_wb = 1'b0;
        this.chan_status_rb = 1'b0;
        this.total_wb_time = 32'h0;
        this.total_rb_time = 32'h0;
        this.total_run_time = 32'h0;
        this.max_used_depth = 32'h0;
        depth_run=0;block_run=0;depth_samples=0;block_samples=0;pushes=0;pops=0;clamped_reads=0;rle_closed=0;
        depth_fd=$fopen({file_inst.file_name,".depth.rle"},"w");
        block_fd=$fopen({file_inst.file_name,".block.rle"},"w");
        if(!depth_fd || !block_fd)$fatal(1,"FIFO_RLE_OPEN_FAILED");
    endfunction

    virtual function void output_to_file();
        logic [31:0] chan_status[5];
        chan_status[0] = {30'h0,this.chan_status_rb,this.chan_status_wb};
        chan_status[1] = this.total_wb_time;
        chan_status[2] = this.total_rb_time;
        chan_status[3] = this.total_run_time;
        chan_status[4] = this.max_used_depth;
        this.chan_file.open_file();
        this.chan_file.dump_1_col(chan_status);
        this.chan_file.finish_dump();
        if(!rle_closed)begin
            if(depth_run)$fwrite(depth_fd,"%0d,%0d\n",depth_run,depth_last);
            if(block_run)$fwrite(block_fd,"%0d,%0d\n",block_run,block_last);
            $fclose(depth_fd);$fclose(block_fd);rle_closed=1;
            $display("DF_FIFO_RLE_SUMMARY file=%s depth_samples=%0d block_samples=%0d end_depth=%0d max_depth=%0d pushes=%0d pops=%0d clamped_reads=%0d",this.file_dumper.file_name,depth_samples,block_samples,this.rt_depth,this.max_used_depth,pushes,pops,clamped_reads);
        end
    endfunction

    virtual task data_monitor();
        fork
            this.record_depth();
            this.record_block();
        join
    endtask

    task record_depth();
        wait (in_intf.reset == 0);
        forever begin
            @(posedge in_intf.clock);
            if(depth_run!=0 && depth_last!==this.rt_depth)begin $fwrite(depth_fd,"%0d,%0d\n",depth_run,depth_last);depth_run=0;end
            if(depth_run==0)depth_last=this.rt_depth;
            depth_run++;depth_samples++;
            if(in_intf.wr_en===1'b1)pushes++;
            if(in_intf.rd_en===1'b1)pops++;
            if(in_intf.rd_en===1'b1 && in_intf.wr_en!==1'b1 && this.rt_depth==0)clamped_reads++;
            if (in_intf.wr_en == 1'b1 && in_intf.rd_en == 1'b1)
                this.rt_depth = this.rt_depth;
            else if (in_intf.wr_en == 1'b1)
                this.rt_depth = this.rt_depth + 32'h1;
            else if (in_intf.rd_en == 1'b1 && this.rt_depth > 32'h0)
                this.rt_depth = this.rt_depth - 32'h1;
            if (this.rt_depth > this.max_used_depth)
                this.max_used_depth = this.rt_depth;
            if (in_intf.finish == 1)
                break;
        end
    endtask

    task record_block();
        wait (in_intf.reset == 0);
        forever begin
            @(posedge in_intf.clock);
            this.total_run_time = this.total_run_time + 32'h1;
            if (in_intf.fifo_wr_block == 1) begin
                begin
                    if(block_run!=0 && block_last!==2'b1)begin $fwrite(block_fd,"%0d,%0d\n",block_run,block_last);block_run=0;end
                    if(block_run==0)block_last=2'b1;
                    block_run++;block_samples++;
                end
                this.chan_status_wb = 1'b1;
                this.total_wb_time = this.total_wb_time + 32'h1;
            end
            else if (in_intf.fifo_rd_block == 1) begin
                begin
                    if(block_run!=0 && block_last!==2'b10)begin $fwrite(block_fd,"%0d,%0d\n",block_run,block_last);block_run=0;end
                    if(block_run==0)block_last=2'b10;
                    block_run++;block_samples++;
                end
                this.chan_status_rb = 1'b1;
                this.total_rb_time = this.total_rb_time + 32'h1;
            end
            else
                begin
                    if(block_run!=0 && block_last!==2'b0)begin $fwrite(block_fd,"%0d,%0d\n",block_run,block_last);block_run=0;end
                    if(block_run==0)block_last=2'b0;
                    block_run++;block_samples++;
                end
            if (in_intf.finish == 1)
                break;
        end
    endtask

    endclass
`endif
