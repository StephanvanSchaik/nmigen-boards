import os
import subprocess

from nmigen.build import *
from nmigen.vendor.xilinx_7series import *
from .resources import *


__all__ = ["PicoEVBPlatform"]


class PicoEVBPlatform(Xilinx7SeriesPlatform):
    device      = "xc7a50t"
    package     = "csg325"
    speed       = "2"
    default_clk = "clk100"
    default_rst = "rst"
    resources   = [
        Resource("clk100", 0, Pins("B6", dir="i"),
            Clock(100e6)),
        Resource("rst", 0, PinsN("A10", dir="i"), Attrs(IOSTANDARD="LVCMOS33", PULLDOWN="true")),

        *LEDResources(pins="V12 V13 V14",
            attrs=Attrs(IOSTANDARD="LVCMOS33", PULLUP="true", DRIVE="8")),

        *SPIFlashResources(0,
            cs_n="L15", clk="-", copi="K16", cipo="L17", wp_n="J15", hold_n="J16",
            attrs=Attrs(IOSTANDARD="LVCMOS33")),
    ]
    connectors  = [
        Connector("gpio", 0, "A12 B12 A13 A14"),
    ]

    def toolchain_prepare(self, fragment, name, **kwargs):
        overrides = {
            "script_after_bitstream":
                "write_cfgmem -format mcs -size 16 -interface SPIx4 -force "
                "-loadbit \"up 0x00000000 {name}.bit\" -file {name}.mcs".format(name=name),
            "add_constraints":
                """
                # Power down when the temperature is too high.
                set_property BITSTREAM.CONFIG.OVERTEMPPOWERDOWN ENABLE [current_design]

                # High-speed configuration so FPGA is up in time to negotiate with PCIe root complex
                set_property BITSTREAM.CONFIG.CONFIGRATE 55 [current_design]
                set_property BITSTREAM.CONFIG_SPI_BUSWIDTH 4 [current_design]
                set_property CONFIG_MODE SPIx4 [current_design]
                set_property BITSTREAM.CONFIG.SPI_FALL_EDGE YES [current_design]
                set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

                set_property CONFIG_VOLTAGE 3.3 [current_design]
                set_property CFGBVS VCCO [current_design]
                """
        }

        return super().toolchain_prepare(fragment, name, **overrides, **kwargs)


if __name__ == "__main__":
    from .test.blinky import *
    PicoEVBPlatform().build(Blinky(), do_program=False)
