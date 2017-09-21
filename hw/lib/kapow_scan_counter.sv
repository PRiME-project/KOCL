//(* altera_attribute = "-name ADV_NETLIST_OPT_ALLOWED NEVER_ALLOW" *)
module kapow_scan_counter(
		input clk, 
		input en, 
		input in, 
		input si,
		output so);

wire [1:0] ff;
dffeas \ff[0] ( 
		.d(in),
		.clk(clk),
		.ena(en),
		.q(ff[0])
);
dffeas \ff[1] ( 
		.d(ff[0]),
		.clk(clk),
		.ena(en),
		.q(ff[1])
);

wire inc;
assign inc = ff[0] & ~ff[1];

parameter nbits = 9;
wire [nbits:0] sdata, q;
genvar i;
generate
	for (i=0; i < nbits; i=i+1) begin : g
		dffeas f(.clk(clk), .ena((en & inc) | ~en), .sload(1'b1), .asdata(sdata[i]), .q(sdata[i+1]));
		defparam f.power_up = "low";
		defparam f.is_wysiwyg = "true";
		defparam f.dont_touch = "true";
	end
	if (nbits == 3)
		assign sdata[0] = ~en ? si :  ~^{sdata[3],sdata[2]};
	else if (nbits == 4)
		assign sdata[0] = ~en ? si :  ~^{sdata[4],sdata[3]};
	else if (nbits == 5)
		assign sdata[0] = ~en ? si :  ~^{sdata[5],sdata[3]};
	else if (nbits == 6)
		assign sdata[0] = ~en ? si :  ~^{sdata[6],sdata[5]};
	else if (nbits == 7)
		assign sdata[0] = ~en ? si :  ~^{sdata[7],sdata[6]};
	else
		assign sdata[0] = ~en ? si :  ~^{sdata[9],sdata[5]};
endgenerate
assign so = sdata[nbits];

endmodule
