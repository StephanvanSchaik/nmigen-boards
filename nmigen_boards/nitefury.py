import os
import subprocess

from nmigen.build import *
from nmigen.vendor.xilinx_7series import *
from .resources import *


__all__ = ["LiteFuryPlatform", "NiteFuryPlatform"]


class _NiteFuryPlatform(Xilinx7SeriesPlatform):
    default_clk = "clk100"
    default_rst = "rst"
    resources   = [
        Resource("clk100", 0, DiffPairs("F6", "E6", dir="i"),
            Clock(100e6), Attrs(IOSTANDARD="LVDS")),
        Resource("clk90", 1, Pins("V22", dir="i"),
            Clock(90e6), Attrs(IOSTANDARD="LVCMOS33")),
        Resource("clk200", 2, DiffPairs("J19", "H19", dir="i"),
            Clock(200e6), Attrs(IOSTANDARD="LVDS_25")),
        Resource("rst", 0, PinsN("J1", dir="i"), Attrs(IOSTANDARD="LVCMOS33")),

        *LEDResources(pins="G3 H3 G4 H4",
            attrs=Attrs(IOSTANDARD="LVCMOS33", PULLUP="true", DRIVE="8")),

        *SPIFlashResources(0,
            cs_n="T19", clk="-", copi="P22", cipo="R22", wp_n="P21", hold_n="R21",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),

        Resource("ddr3", 0,
            Subsignal("rst",     PinsN("K16", dir="o"), Attrs(IOSTANDARD="LVCMOS15")),
            Subsignal("clk",     DiffPairs("K17", "J17", dir="o"), Attrs(IOSTANDARD="DIFF_SSTL15")),
            Subsignal("clk_en",  Pins("H22", dir="o")),
            Subsignal("we",      PinsN("L16", dir="o")),
            Subsignal("ras",     PinsN("H20", dir="o")),
            Subsignal("cas",     PinsN("K18", dir="o")),
            Subsignal("a",       Pins("M15 L21 M16 L18 K21 M18 M21 N20 M20 N19 J21 M22 K22 N18 N22 J22", dir="o")),
            Subsignal("ba",      Pins("L19 J20 L20", dir="o")),
            Subsignal("dqs",     DiffPairs("F18 B21", "E18 A21", dir="io"), Attrs(IOSTANDARD="DIFF_SSTL15")),
            Subsignal("dq",      Pins("D19 B20 E19 A20 F19 C19 F20 C18 E22 G21 D20 E21 C22 D21 B22 D22", dir="io")),
            Subsignal("dm",      Pins("A19 G22", dir="o")),
            Subsignal("odt",     Pins("K19", dir="o")),
            Attrs(IOSTANDARD="SSTL15")
        )
    ]
    connectors  = [
        Connector("gpio", 0, "J5 H5 K2 J2"),
    ]

    def toolchain_prepare(self, fragment, name, **kwargs):
        overrides = {
            "script_after_bitstream":
                "write_cfgmem -format mcs -size 16 -interface SPIx4 -force "
                "-loadbit \"up 0x00000000 {name}.bit\" -file {name}.mcs".format(name=name),
            "add_constraints":
                """
                # Input reset is resynchronized within FPGA design as necessary.
                set_false_path -from [get_ports rst_0__io]

                # Power down when the temperature is too high.
                set_property BITSTREAM.CONFIG.OVERTEMPPOWERDOWN ENABLE [current_design]

                # High-speed configuration so FPGA is up in time to negotiate with PCIe root complex
                set_property BITSTREAM.CONFIG_EXTMASTERCCLK_EN Div-1 [current_design]
                set_property BITSTREAM.CONFIG_SPI_BUSWIDTH 4 [current_design]
                set_property CONFIG_MODE SPIx4 [current_design]
                set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES [current_design]
                set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

                set_property CONFIG_VOLTAGE 3.3 [current_design]
                set_property CFGBVS VCCO [current_design]
                """
        }

        return super().toolchain_prepare(fragment, name, **overrides, **kwargs)


class LiteFuryPlatform(_NiteFuryPlatform):
    device      = "xc7a100t"
    package     = "fgg484"
    speed       = "2L"


class NiteFuryPlatform(_NiteFuryPlatform):
    device      = "xc7a200t"
    package     = "fbg484"
    speed       = "3"


if __name__ == "__main__":
    from .test.blinky import *
    LiteFuryPlatform().build(Blinky(), do_program=False)
