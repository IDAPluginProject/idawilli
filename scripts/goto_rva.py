import ida_kernwin
import ida_nalt


def main():
    rva = ida_kernwin.ask_addr(0x0, "RVA")
    if not rva:
        return

    ida_kernwin.jumpto(ida_nalt.get_imagebase() + rva)


main()
