import re

with open('f:/anas/موقع/nile-manhwa/data.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix truncation by appending the proper closing blocks
appendix = '''    ]
}
/* LATEST_MANGA_END */
        ]
    },
    manhwa: {
        topSlider: [],
        trending: [],
        latest: [
/* LATEST_MANHWA_START */

/* LATEST_MANHWA_END */
        ]
    }
};
'''

# Ensure we don't append multiple times
if 'manhwa: {' not in text:
    with open('f:/anas/موقع/nile-manhwa/data.js', 'a', encoding='utf-8') as f:
        f.write(appendix)
    print('Successfully appended missing file ending.')
