-- PRiME KAPow control QSys component
-- Controls KAPow instrumentation
-- James Davis, 2015

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library altera_mf;
use altera_mf.all;

entity kapow_ctrl is
	generic(
		kernel_hash: natural := 0;
		n: natural := 8;
		w: natural := 9;
		meta_stages: natural := 2																	-- Number of metastability register stages to use in clock domain-crossing. Must be >= 2
	);
	port(
		clk: in std_logic;
		rstn: in std_logic;
		bus_address: in std_logic_vector(2 downto 0);
		bus_read: in std_logic;
		bus_readdata: out std_logic_vector(31 downto 0);
		bus_waitrequest: out std_logic;
		bus_write: in std_logic;
		bus_writedata: in std_logic_vector(31 downto 0);
		kapow_clk: in std_logic;
		kapow_cnten: out std_logic;
		kapow_scanin: out std_logic;
		kapow_scanout: in std_logic
	);
end entity kapow_ctrl;

architecture rtl of kapow_ctrl is
	
	signal ttl: std_logic_vector(15 downto 0);
	signal cnt_en: std_logic;
	
	signal cnt_en_req: std_logic_vector(meta_stages + 1 downto 0);
	signal cnt_en_ack: std_logic_vector(meta_stages - 1 downto 0);
	attribute altera_attribute: string;
	attribute altera_attribute of cnt_en_req: signal is "-name AUTO_SHIFT_REGISTER_RECOGNITION OFF; -name SYNCHRONIZER_IDENTIFICATION FORCED";
	attribute altera_attribute of cnt_en_ack: signal is "-name AUTO_SHIFT_REGISTER_RECOGNITION OFF; -name SYNCHRONIZER_IDENTIFICATION FORCED";
	
	signal fifo_data: std_logic_vector(0 downto 0);
	signal fifo_pop: std_logic;
	signal fifo_push: std_logic;
	signal fifo_dataout: std_logic_vector(31 downto 0);
	signal fifo_empty: std_logic;
	signal fifo_full: std_logic;
	
	component dcfifo_mixed_widths
		generic(
			intended_device_family: string;
			lpm_numwords: natural;
			lpm_showahead: string;
			lpm_width: natural;
			lpm_widthu: natural;
			lpm_widthu_r: natural;
			lpm_width_r: natural;
			rdsync_delaypipe: natural;
			wrsync_delaypipe: natural
		);
		port(
			data: in std_logic_vector(0 downto 0);
			rdclk: in std_logic;
			rdreq: in std_logic;
			wrclk: in std_logic;
			wrreq: in std_logic;
			q: out std_logic_vector(31 downto 0);
			rdempty: out std_logic
		);
	end component dcfifo_mixed_widths;
	
	component altsyncram
		generic(
			clock_enable_input_a: string;
			clock_enable_output_a: string;
			init_file: string;
			intended_device_family: string;
			lpm_hint: string;
			lpm_type: string;
			numwords_a: natural;
			operation_mode: string;
			widthad_a: natural;
			width_a: natural
		);
		port(
			address_a: in std_logic_vector(0 downto 0);
			clock0: in std_logic;
			q_a: out std_logic_vector(15 downto 0)
		);
	end component altsyncram;

begin
	
	ttl_rom: altsyncram
		generic map(
			clock_enable_input_a => "BYPASS",
			clock_enable_output_a => "BYPASS",
			init_file => "kapow_ttl.mif",
			intended_device_family => "Cyclone V",
			lpm_hint => "ENABLE_RUNTIME_MOD=NO",
			lpm_type => "altsyncram",
			numwords_a => 1,
			operation_mode => "ROM",
			widthad_a => 1,
			width_a => 16
		)
		port map(
			address_a => (others => '0'),
			clock0 => clk,
			q_a => ttl
		);
	
	bus_comb_proc: process(rstn, bus_read, bus_address, fifo_empty, fifo_dataout)
	begin
		bus_readdata <= x"deadbeef";
		bus_waitrequest <= '0';
		fifo_pop <= '0';
		if rstn = '1' then
			if bus_read = '1' then
				case bus_address is
					when "000" =>																	-- Read address 0: return KAPow ID stamp, which is hex(md5('KAPow'))[-8:] = 0x7f323e2e
						bus_readdata <= x"7f323e2e";
					when "001" =>																	-- Read address 1: return hash of the associated kernel passed in via QSys using generic kernel_hash
						bus_readdata <= std_logic_vector(to_unsigned(kernel_hash, 32));
					when "010" =>																	-- Read address 2: return N as passed in via QSys using generic n
						bus_readdata <= std_logic_vector(to_unsigned(n, 32));
					when "011" =>																	-- Read address 3: return W as passed in via QSys using generic w
						bus_readdata <= std_logic_vector(to_unsigned(w, 32));
					when "101" =>																	-- Read address 5: return the value dangling out of the FIFO, if it's valid
						if fifo_empty = '0' then
							bus_readdata <= fifo_dataout;
							fifo_pop <= '1';
						else
							bus_waitrequest <= '1';
						end if;
					when others =>
						null;
				end case;
			end if;
		else
			bus_waitrequest <= '1';
		end if;
	end process bus_comb_proc;
	
	bus_seq_proc: process
		variable cnt: integer range 0 to 2**16 - 1;
	begin
		wait until clk'event and clk = '1';
		cnt_en <= '0';
		if rstn = '1' then
			if bus_write = '1' then
				if bus_address = "100" then															-- Write address 4: set number of cycles for measurement period (TTL) and start counting
					cnt := to_integer(unsigned(ttl));
				end if;
			end if;
			if cnt > 0 then
				cnt := cnt - 1;
				cnt_en <= '1';
			end if;
		else
			cnt := 0;
		end if;
	end process bus_seq_proc;
	
	cnt_en_bus_proc: process																		-- cnt_en handshaking into kapow_clk domain
	begin
		wait until clk'event and clk = '1';
		if cnt_en_req(cnt_en_req'high) = cnt_en_ack(0) then
			cnt_en_req(cnt_en_req'high) <= cnt_en;
		end if;
		cnt_en_ack <= cnt_en_req(1) & cnt_en_ack(cnt_en_ack'high downto 1);
	end process cnt_en_bus_proc;
	
	cnt_en_kapow_proc: process
	begin
		wait until kapow_clk'event and kapow_clk = '1';
		cnt_en_req(cnt_en_req'high - 1 downto 0) <= cnt_en_req(cnt_en_req'high downto 1);
	end process cnt_en_kapow_proc;
	kapow_cnten <= cnt_en_req(0);
	
	kapow_fifo: dcfifo_mixed_widths
		generic map(
			intended_device_family => "Cyclone V",
			lpm_numwords => 2**integer(ceil(log2(real(n*w)))),
			lpm_showahead => "ON",
			lpm_width => 1,
			lpm_widthu => integer(ceil(log2(real(n*w)))),
			lpm_widthu_r => integer(ceil(log2(real(n*w)))) - 5,
			lpm_width_r => 32,
			rdsync_delaypipe => meta_stages + 2,
			wrsync_delaypipe => meta_stages + 2
		)
		port map(
			data => fifo_data,
			rdclk => clk,
			rdreq => fifo_pop,
			wrclk => kapow_clk,
			wrreq => fifo_push,
			q => fifo_dataout,
			rdempty => fifo_empty
		);
	fifo_data(0) <= kapow_scanout;
	
	fifo_push_proc: process																			-- Start pushing data into the FIFO as soon as cnt_en_req(0) goes low, stopping after lpm_numwords cycles
		variable cnt: integer range 0 to 2**integer(ceil(log2(real(n*w))));
	begin
		wait until kapow_clk'event and kapow_clk = '1';
		fifo_push <= '0';
		if cnt_en_req(1) = '0' and cnt_en_req(0) = '1' then
			cnt := 2**integer(ceil(log2(real(n*w))));
		end if;
		if cnt > 0 then
			cnt := cnt - 1;
			fifo_push <= '1';
		end if;
	end process fifo_push_proc;

	kapow_scanin <= '0';																			-- Hold scan chain input low to reset activity counters as their data is scanned out
	
end architecture rtl;