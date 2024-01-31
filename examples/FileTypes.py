# imghdr.what() does not test correctly,
# these tests were added for another project,
# but it makes sense to ignore that library 
# since we have additions and deletions and
# fixes, just do it here

def is_media(header=None, extension=None, extensions = None):
    if extension is None and header is None:
        print("TODO: error")
    if extensions is None:
        extensions = ["jpg", "png", "gif", "webp", "tiff"] # "ppm", "pgm"
    if extension is None:
        extension = get_filetype(header)
    if extension in extensions:
        return True
    return False

# TODO: add length tests, and if possible order tests by length
def get_filetype(h):

    if (h[:3] == b'\xff\xd8\xff'):
        return "jpg"
    if h[6:10] in (b'JFIF', b'Exif'):
        return "jpg"

    if h.startswith(b'\211PNG\r\n\032\n'):
        return "png"

    if h[:6] in (b'GIF87a', b'GIF89a'):
        return "gif"

    if h[:2] in (b'MM', b'II'):
        return "tiff"

    if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return "webp"

    if len(h) > 2 and h[0] == ord(b'P'):
        if h[1] in b'14' and h[2] in b' \t\n\r':
            return "ppm"
        if h[1] in b'25' and h[2] in b' \t\n\r':
            return "pgm"
        if h[1] in b'36' and h[2] in b' \t\n\r':
            return "ppm"

    # includes the Signature Box identifier and contents and the File Type Box identifier ("ftypjp2")
    # maybe trust the "ftyp" value if it's alphanum
    # this is JP2. similar formats JPX and JPM could have jpx or jpm here, or not.
    # I think there's also a mandatory space after the identifier(s) so ["ftypjp2 ", "ftypjpx ", "ftypjpm "]
    # if that's correct, simplify these tests
    if len(h) > 23:
        if h[:23] == b'\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A\x00\x00\x00\x14\x66\x74\x79\x70\x6A\x70\x32':
            return "jp2"
    if len(h) > 23:
        if h[:23] == b'\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A\x00\x00\x00\x14\x66\x74\x79\x70\x6A\x70\x78':
            return "jpx"
    if len(h) > 23:
        if h[:23] == b'\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A\x00\x00\x00\x14\x66\x74\x79\x70\x6A\x70\x6D':
            return "jpm"

    if b"<html" in h:
        return "html"
    if b"<HTML" in h:
        return "html"
    if b"<!DOCTYPE " in h: # "<!DOCTYPE HTML" or "<!DOCTYPE html"
        return "html"
    if b"<!doctype html" in h:
        return "html"

    if b"<xml" in h:
        return "xml"
    if b"<?xml " in h:
        return "xml"

    return None
