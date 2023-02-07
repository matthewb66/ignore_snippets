# Synopsys Ignore Snippets Script - ignore_snippets.py
# INTRODUCTION

This script is provided under an OSS license as an example of how to use the Black Duck APIs to ignore snippet matches.

It does not represent any extension of licensed functionality of Synopsys software itself and is provided as-is, without warranty or liability.

# DESCRIPTION

The `ignore_snippets.py` script ignores (or unignores) unconfirmed snippet matches selected by specified options.

Snippets can be selected by one or more of the minimum match score (which is a hybrid score combining the match level with the likelihood that the component can be copied), the minimum coverage score (the percentage of matching lines), the minimum file size (in bytes), or the minimum count of matched lines. Multiple options are combined (AND).

A report option allows listing all of the match values without ignoring/unignoring.

An additional option changes ignore to unignore (to undo a previous ignore activity).

# PREREQUISITES

Python 3 and the Black Duck https://github.com/blackducksoftware/hub-rest-api-python package must be installed and configured to enable the Python API scripts for Black Duck prior to using this script.

A Black Duck API key with read/write permissions must be configured in a token file.

# INSTALLATION

Install the hub-rest-api-python package from [PyPi](https://pypi.org/project/blackduck/):

    pip3 install blackduck

Create a token file containing a Black Duck API token.

# USAGE

The `ignore_snippets.py` script can be invoked as follows:

    usage: ignore_snippets.py [-h] [-s SCOREMIN] [-c COVERAGEMIN]
                               [-z SIZEMIN] [-l MATCHEDLINESMIN] [-r] [-u] [--no-verify]
                               base_url token_file project_name version_name
                               
    Ignore (or unignore) snippets int he specified project/version using the supplied
    options. Running with no options apart from url, token file, project and version will cause all
    snippets to be ignored.

    positional arguments:
        base_url              Black Duck server URL e.g. https://your.blackduck.url
        token_file            Name of the file containing a Black Duck API token
        project_name          Black Duck project name
        version_name          Black Duck version name

    optional arguments:
        -h, --help            show this help message and exit
        -s SCOREMIN, --scoremin SCOREMIN
                              Minimum match score percentage value (hybrid value of
                              snippet match and likelihood that component can be
                              copied)
       -c COVERAGEMIN, --coveragemin COVERAGEMIN
                              Minimum matched lines percentage
       -z SIZEMIN, --sizemin SIZEMIN
                              Minimum source file size (in bytes)
       -l MATCHEDLINESMIN, --matchedlinesmin MATCHEDLINESMIN
                              Minimum number of matched lines from source file
       -r, --report           Report the snippet match values, do not
                              ignore/unignore
       -u, --unignore         Unignore matched snippets (undo ignore action)
       --no-verify            Disable TLS certificate verification

# EXAMPLE EXECUTION

The example project/version (partisan-snippets/1.0) contains 4 unignored/unconfirmed snippets.

The --report option will list the snippet match values for all snippets (but will not ignore/unignore):

    python3 ignore_snippets.py https://your.blackduck.url token.txt partisan-snippets 1.0 --report
    
    File: myfile.erl (size = 7149)
        Block 1: matchScore = 37%, matchCoverage = 51%, matchedLines = 97 - Would be ignored
    File: partisan_acknowledgement_backend.erl (size = 3143)
        Block 1: matchScore = 42%, matchCoverage = 24%, matchedLines = 12 - Would be ignored
    File: partisan_analysis.erl (size = 42006)
        Block 1: matchScore = 35%, matchCoverage = 1%, matchedLines = 12 - Would be ignored
    File: partisan_app.erl (size = 1231)
        Block 1: matchScore = 54%, matchCoverage = 100%, matchedLines = 38 - Would be ignored

Running the script specifying just the project and version name will cause all snippets to be ignored:

    python3 ignore_snippets.py https://your.blackduck.url token.txt partisan-snippets 1.0
    
    File: myfile.erl - Ignored
    File: partisan_acknowledgement_backend.erl - Ignored
    File: partisan_analysis.erl - Ignored
    File: partisan_app.erl - Ignored

Specifying the --unignore (or -u) option will cause all snippets to be UNignored:

    python3 ignore_snippets.py https://your.blackduck.url token.txt partisan-snippets 1.0 --unignore
    
    File: myfile.erl - Unignored
    File: partisan_acknowledgement_backend.erl - Unignored
    File: partisan_analysis.erl - Unignored
    File: partisan_app.erl - Unignored
    
The following examples ignores snippets with a maximum coverage (matched line percentage) of 50% and a maximum matched line count of 20:

    python3 ignore_snippets.py https://your.blackduck.url token.txt partisan-snippets 1.0 -c 50 -l 20

    File: partisan_acknowledgement_backend.erl - Ignored
    File: partisan_analysis.erl - Ignored
