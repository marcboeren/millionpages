
# millionpages

version 0.0001, concept

## static site generator

### quick what's what

Manage your content in the `site` folder. The folder hierarchy will be the urls for the generated static site. Any markdown (`.md`) file in the hierarchy will be the canonical url for that page (without extension). Files and folders starting with an underscore (`_`) will not be copied to the generated static site, the rest is copied as-is. Files named `__index__.yaml`, also pronounced as 'dunder-index') have special meaning, they are configuration files that generate `index` pages and sub-urls based on pages content. More on that later.

Layout and style is managed in the `theme` folder. The contents of the `theme` folder is copied to the generated static site as well, following the same don't-copy-the-underscored-ones pattern. That's why the `_templates` folder starts with an underscore; we don't want to publish the raw templates.

Finally, after generation, you can upload everything under `upload-generated-site` to the public folder of your website.

The configuration for the site, and the site-wide parameters, is set in the top-level `__site__.yaml` config file. This also specifies the folders named above; if you want to use your own names, please don't, but if you really really want to, go ahead.

Quick example of how a site + theme folder...

    site
        images
            calvin.gif
            hobbes.png
        __index__.yaml
        hello-world.md
        robots.txt

    theme
        _templates
        style
            logo.svg
            site.css
            site.js
        favicon.ico

...translates to the generated site url hierarchy:

    /
    /hello-world
    /images
        calvin.gif
        hobbes.png
    /style
        logo.svg
        site.css
        site.js
    /favicon.ico
    /robots.txt


### pages

Every markdown file in the site folder and subfolders translates to a page. The name is used as the url, so `/hello-world.md` becomes `/hello-world`. Folder names are preserved, so `/hello/world.md` becomes `/hello/world`. They have no special meaning beyond this, though.

Every folder, including the `site` root folder, will have an index page. This will be generated from the `__index__.yaml` file, unless an `index.md` page is present, then that one will be used. So, `/hello-world/index.md` becomes `/hello-world`. This is useful if you use subfolders to make `/hello-world/its-me/how-are-you`.

If you want to associate parameters with pages, you can precede the markdown content with `front-matter`, which is in yaml format. Start the page with three dashes on a single line, add your yaml, again a single line with three dashes, and then your markdown. An example:

    ---
    type: post
    title: Hello, world!
    date: 2018-12-04
    tags:
    - hello
    - world
    ---

    # Hello, world!

    It's me! How are you?

Now we have four parameters for this page, `type`, `title`, `date`, and `tags`. These are available in the templates (as `{{ page.config.title }}`), but can also be used in `__index__.yaml` configurations to filter and group the complete collection of pages.


### \_\_index\_\_.yaml

The `__index__.yaml` file is used to generate an index page, which is a list pointing to the matching pages or groups. A secondary function is to create groups of pages, a sort of sub-index if you will. This can be nested too.

Let's see an example first:

    title: Hello, world!
    pages:
      order: date desc

Or:

    title: Hello, blog!
    pages:
      filter:
        type: post
      order: date desc
      groups:
        - by: tags
          order: title asc

The first one will simply have a list of all the pages available in the template. The second one will, through the `groups` directive, also generate a list of folders. So for this simple one-page (`/hello-world.md`) site, we'll get:

    /
    /hello-world
    /hello
    /hello/hello-world
    /world
    /world/hello-world

To avoid duplicated content SEO-punishment, the `hello-world` pages in the `hello` and `world` subfolders will hava a canonical link to the root one (as that is where it appears in the `site` folder).

For nesting, we add a `pages` directive inside a `groups` directive, and since `pages` can contains `groups` we can nest ad infinitum. Example time:

    title: Hello, blog!
    pages:
      filter:
        type: post
      order: date desc
      groups:
        - by: tags
          title: "Indexed by {{ group.value }}"
          order: title asc
          pages:
            filter:
              date: from 2018-01-01
            order: date desc
            groups:
              - by: keywords
                title: "Recent files, indexed by {{ group.value }}"

Now all the pages that are in each of the `tags` folders are filtered on `date`, and the result is grouped by `keywords`. You've probably noted that you need to add a `keywords` parameter to the `front-matter` for this example.

### internal links

Always use root-relative urls for internal links to pages or files, so `/hello/hello-world` or `/style/logo.svg`, not `logo.svg` or `subfolder/file.ext`.

This goes for page markdown, page front-matter, yaml configs, and theme templates.


### templates

We use Jinja2 for templating, and all templates are relative to the `theme/_templates` folder. See [the Jinja2 documentation](http://jinja.pocoo.org/docs/2.10/templates/) for the details.

The two default templates are `page.html` and `index.html`. These extend the `site.html` base template. If you specify a `template` parameter in the page front-matter or the index configuration, then that one will be used instead.


#### template variables

Template variables look like `{{ page.config.title }}`. For the page, all parameters are available with dot-notation, starting from the `page` context. On an index page, parameters are available from the `index` context, so `{{ index.pages }}` will have a list of the matching pages. If you're also expecting a `site` context, you will be right. You've probably spotted a `group` context too then, smartypants.

Besides in templates, you can use template variables in front-matter (properly quoted, because `{}` characters have special meaning in yaml) and in markdown content.


### image resizing

In a responsive design (or any design, really) you'll need multiple versions of the same image, for example a thumbnail and a hero, or a phone and desktop variant. Millionpages supports image resizing so you can work from a single, high resolution original.

In the templates, you can either specify an image by path (`/images/hobbes.png`) or through a variable (`{{ page.image }}`). If you want a specific width in your template, say 400 points, you must enter this in the path (`/images/hobbes@400w.png`) or add a resize filter to the variable (`{{ page.image|resize(400) }}`). The height is then based on the aspect ratio of the original. If you wish an exact size, specify both width and height in the path (`/images/hobbes@400w300h.png`) or the resize filter (`{{ page.image|resize(400, 300) }}`). The original is scaled to cover the entire area, so some cropping may occur. The center of the image will be the center of the resized image.

Note we said 400 points, not pixels. For high resolution devices, the actual pixels will be a multiple of the points. Think of points as the @1x version, and use that in all the templates. High resolution versions will be created and used automatically, up to a maximum of the original (means we never scale up, only down).

_experimental_

When specifying both width and height, you can add a focal point which will be as close to the center of the resized image as possible. The focal point is given as ratios along the horizontal (x-) and vertical (y-) axis of the original image, with the origin in the bottom-left corner (0.0, 0.0) and (1.0, 1.0) is the top-right corner. So the center will always have a value of (0.5, 0.5).

To put this into practice, use path (`/images/hobbes@400w300h0.5x0.5y.png`) or the resize filter (`{{ page.image|resize(400, 300, x=0.5, y=0.5) }}`).

#### note

Please don't name your original image files with an `@`-sign somewhere in the name, who knows what horrible scenarios might ensue.


### minify javascript and stylesheets

_experimental_

To minimize the number of requests per page as well as the download size, we can concatenate and minify the javascript and stylesheets inside your `theme` folder or subfolders thereof.

For each folder we collect the `.js` files starting with an underscore (remember, they don't get copied to the generated site), sort them alphabetically, concatenate them, minify the result, and put that file in the corresponding folder for the generated site with the name `_index.js`. Always use this link in your templates, and not the regular underscored filenames.

The same technique applies to `.css` files, resulting in `_index.css`.

For example, your `theme` folder...

    _templates
    style
        logo.svg
        _01.jquery.js
        _02.plugin.js
        _99.site.js
        _01.reset.css
        _02.plugin.css
        _99.site.css
    favicon.ico

...will result in

    style
        logo.svg
        _index.js
        _index.css
    favicon.ico


### search

_experimental_

If we make a word list (and combined word list) and publish it as a json file with each entry pointing to the canonical url, we can use javascript to build autocomplete search. If the number of words or pages get very large, we can split this index in multiple files, one for each start letter for example. If we put this file in a `_api` folder in the generated site, it can't clash with other names because underscored files and folders aren't published.
