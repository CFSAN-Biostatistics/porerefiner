from . import SnifferFor, ParserFor


if __name__ == '__main__':
    # test parsers
    from . import sniffers
    for name, sniffer in SnifferFor.sniffers.items():
        parser = ParserFor.parsers[sniffer]
        rows = [line.split('\t') for line in sniffer.__doc__.split('\n')]
        try:
            print(name, "->", parser.__doc__)
            assert sniffer(rows)
            parser(rows)
        except AssertionError:
            print(name, "couldn't recognize its own format")
            print(rows)
        except:
            print(rows)
            raise
    print("Test sniffers complete")