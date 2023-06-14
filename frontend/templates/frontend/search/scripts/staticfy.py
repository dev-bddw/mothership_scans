import fileinput
import os

"""
this is a small app to help you change your
react files to django static files
place in the application root
"""


"""
TBI:
    look at the index.html (django template)
    move the css and js dependencies to the css/jss template block

"""


def static_my_react_dependences(path_tuple):
    """
    take the dir / asset dir
    find the files in asset dir
    then use them to replace the src dependencis lines in
    index.html
    """
    index, assets = path_tuple
    assets_list = os.listdir(assets)

    # get the file names from the assets directory
    js = assets_list[0] if assets_list[0].endswith(".js") else assets_list[1]
    css = assets_list[1] if assets_list[1].endswith(".css") else assets_list[0]

    js_boil = '<script type="module" crossorigin src="#"></script>'
    css_boil = '<link rel="stylesheet" href="#">'

    # build the lines you're expecting to see
    js_old = f'<script type="module" crossorigin src="/assets/{js}"></script>'
    js_new = (
        '<script type="module" crossorigin src="BB% static "{0}" %BE"></script>'.format(
            js
        )
        .replace("BB", "{")
        .replace("BE", "}")
    )  # noqa

    css_old = f'<link rel="stylesheet" href="/assets/{css}">'
    css_new = (
        '<link rel="stylesheet" href="BB% static "{0}" %BE">'.format(css)
        .replace("BB", "{")
        .replace("BE", "}")
    )

    # remove the non static urls from the top of the file (vite puts them there)
    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # remove line matching the old js that we saved to memory already
            print(line.replace(js_old, ""), end="")

    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # replace line matching the old css that we saved to memory already
            print(line.replace(css_old, ""), end="")

    # replace the boiler plate with that non-static urls first
    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # replace the js path html tag with django url tag
            print(line.replace(js_boil, js_old), end="")

    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # replace the css path html tag with django url tag
            print(line.replace(css_boil, css_old), end="")

    # replace the no-static urls with django tags
    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # replace the js path html tag with django url tag
            print(line.replace(js_old, js_new), end="")

    with fileinput.FileInput(index, inplace=True, backup=".bak") as file:
        for line in file:
            # replace the css path html tag with django url tag
            print(line.replace(css_old, css_new), end="")

    print(f"Successfully altered {index}")


if __name__ == "__main__":

    print("Starting replace...")

    path = ("dist/index.html", "dist/assets/")

    # paths = [
    #    (cwd + x + "dist/index.html", cwd + x + "dist/assets/") for x in template_dirs
    # ]
    static_my_react_dependences(path)
    print("Replace complete.")
