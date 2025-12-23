import os

# שם הקובץ לתיקון
filename = "arith.c"

try:
    with open(filename, "r") as f:
        content = f.read()

    # החלפת הנתיבים השגויים בנתיבים מקומיים
    # מחליף את "lib/errhand.h" ב-"errhand.h"
    new_content = content.replace('#include "lib/errhand.h"', '#include "errhand.h"')
    # מחליף את "lib/bitio.h" ב-"bitio.h" (למקרה שגם זה קיים)
    new_content = new_content.replace('#include "lib/bitio.h"', '#include "bitio.h"')

    with open(filename, "w") as f:
        f.write(new_content)

    print(f"Successfully fixed include paths in {filename}")

except FileNotFoundError:
    print(f"Error: {filename} not found in current directory.")
except Exception as e:
    print(f"An error occurred: {e}")