import subprocess


def rofi(prompt, options, rofi_args=None, fuzzy=True):
    args = ['rofi', '-dmenu', '-p', prompt, '-format', 's', '-i']
    if fuzzy:
        args += ['-matching', 'fuzzy']
    args += list(rofi_args or [])
    result = subprocess.run([str(arg) for arg in args],
                            input='\n'.join(opt.replace('\n', ' ') for opt in options),
                            capture_output=True, text=True)
    selected = result.stdout.strip()
    if result.returncode == 1:
        return -1, -1, ''
    if result.returncode != 0:
        raise RuntimeError(f'Rofi falhou ({result.returncode}): {result.stderr.strip()}')
    try:
        index = [opt.strip() for opt in options].index(selected)
    except ValueError:
        index = -1
    return 0, index, selected
