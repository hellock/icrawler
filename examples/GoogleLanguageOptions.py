# from https://www.google.com/support/enterprise/static/gsa/docs/admin/current/gsa_doc_set/xml_reference/request_format.html#1077441
# numbers are just the html fragment, preserved so the html can be simply modified if it changes, discard the numbers
# querystring is "&lr=lang_en", the lang_ prefix is discarded here, see google.py
# see also &ie=latin1&oe=latin1

# format: "lang_" + { ISO 639-1 Code }
google_languages = [
    [0, "          ", 0, "          "], # first option blank to allow un-select
    [1077328, "Arabic", 1077330, "ar"],
    [1077332, "Chinese (Simplified)", 1077334, "zh-CN"],
    [1077336, "Chinese (Traditional)", 1077338, "zh-TW"],
    [1077340, "Czech", 1077342, "cs"],
    [1077344, "Danish", 1077346, "da"],
    [1077348, "Dutch", 1077350, "nl"],
    [1077352, "English", 1077354, "en"],
    [1077356, "Estonian", 1077358, "et"],
    [1077360, "Finnish", 1077362, "fi"],
    [1077364, "French", 1077366, "fr"],
    [1077368, "German", 1077370, "de"],
    [1077372, "Greek", 1077374, "el"],
    [1077376, "Hebrew", 1077378, "iw"],
    [1077380, "Hungarian", 1077382, "hu"],
    [1077384, "Icelandic", 1077386, "is"],
    [1077388, "Italian", 1077390, "it"],
    [1077392, "Japanese", 1077394, "ja"],
    [1077396, "Korean", 1077398, "ko"],
    [1077400, "Latvian", 1077402, "lv"],
    [1077404, "Lithuanian", 1077406, "lt"],
    [1077408, "Norwegian", 1077410, "no"],
    [1077412, "Portuguese", 1077414, "pt"],
    [1077416, "Polish", 1077418, "pl"],
    [1077420, "Romanian", 1077422, "ro"],
    [1077424, "Russian", 1077426, "ru"],
    [1077428, "Spanish", 1077430, "es"],
    [1077432, "Swedish", 1077434, "sv"],
    [1077436, "Turkish", 1077438, "tr"],
]

# TODO: put this in a class
google_language_dict= {}
for i in range(len(google_languages)):
    google_language_dict[google_languages[i][1]] = google_languages[i][3]
