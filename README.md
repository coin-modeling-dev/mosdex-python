# mosdex-python

A Python demonstration of the MOSDEX standard for large-scale modular optimization problems.  It is based on an experimental version of the MOSDEX Schema, which is still being refined.  The MOSDEX standard is documented in the repository https://github.com/coin-modeling-dev/MOSDEX-Examples.

This demonstration uses a development JSON schema which is included in the `data` directory, along with a `sailco` file that tests it.
* To install the mosdex-python package and dependencies: `pip install mosdex-python`
* Example code is in the `samples` directory. To run sailco: `cd samples; python -m sailco`
* PDFs of some sample output are in `mosdex-python/data`

Wish list:
* Syntax to describe functional relationships between independent and dependent variables
* Syntax to describe sequence operators: `next` and `previous`
* Interfaces to some modeling languages

Acknowledgements: This effort was initiated during workshops hosted by the Institute for Mathematics and its Applications at the Unversity of Minnesota https://www.ima.umn.edu/ and organized by the COIN-OR Foundation https://www.coin-or.org/

Team: Jeremy Bloom <jeremybloomca@gmail.com>, Alan King <kingaj@us.ibm.com>, Matt Saltman <mjs@clemson.edu>, Brad Bell <bradbell@seanet.com>
Slack channel: coin-or.slack.com/#ima-modeling-sprint
