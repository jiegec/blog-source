---
layout: post
date: 2017-06-15 17:22:20 +0800
tags: [macos,karabiner-elements,keyboard]
category: system
title: In macOS Sierra, Karabiner-Elements finally support complex modifications
---

In favor of this [commit](https://github.com/tekezo/Karabiner-Elements/commit/f37815dcf58fd1e91d3cd3d154c2ed3749a2510e), Karabiner-Elements now supports the much welcomed yet long-lost feature, namely complex modifications that enable users to trigger complex keypress.

Now I can achieve this:
```
If I press <Enter>, then:
1. If <Enter> is pressed alone, then send <Enter>.
2. If <Enter> is pressed along with other keys, then send <Control> + Other.
```

By adding this code to ~/.config/karabiner/karabiner.json :
```
"complex_modifications": {
    "rules": [
        {
            "manipulators": [
                {
                    "description": "Change return_or_enter to left_control. (Post return_or_enter if pressed alone)",
                    "from": {
                        "key_code": "return_or_enter",
                        "modifiers": {
                            "optional": [
                                "any"
                            ]
                        }
                    },
                    "to": [
                        {
                            "key_code": "left_control"
                        }
                    ],
                    "to_if_alone": [
                        {
                            "key_code": "return_or_enter"
                        }
                    ],
                    "type": "basic"
                }
            ]
        }
    ]
},
```
in one of profiles.

Note: the snippet above is adopted from [this example](https://github.com/tekezo/Karabiner-Elements/blob/61df6ff04ce34adf1cbb00cfd7c5dd49c14c0889/examples/spacebar_to_shift.json). You can explore more examples since the GUI is not updated accordingly yet.

Important: Until NOW (2017-06-15), this feature is only implemented in beta versions of Karabiner-Elements (at least 0.91.1).
