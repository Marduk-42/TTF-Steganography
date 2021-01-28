# TTF-Steganography
A pure-python module to apply Least Significant Bit(s) Steganography to TrueType font files


Hide binary data to a file:
```
ttf_file = LSB(ttf_path)
ttf_file.hide(your_binary_data, path_to_hide) 
```
Recover binary data from a file:
```
ttf_file = LSB(ttf_path)
your_binary_data = ttf_file.recover()
```

The module uses LSB to hide the data, further methods like Value Differencing will be added soon.
If you want to hide more than one bit per coordinate, use the parameter 'change':
```
ttf_file.hide(your_binary_data, path_to_hide, change=3)
```
Now the last three bits will be changed, which shouldn't be detectable to the human eye.

If you need to hide/recover more than 1MB (or 2^23 bits), set META_DATA_LENGTH higher.
