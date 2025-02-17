#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to filter streamlines based on their lengths.

See also:
    - scil_tractogram_detect_loops.py
    - scil_tractogram_filter_by_anatomy.py
        (Filtering by length is its step1)
    - scil_tractogram_filter_by_orientation.py
    - scil_tractogram_filter_by_roi.py

Formerly: scil_filter_streamlines_by_length.py
"""

import argparse
import json
import logging

import numpy as np

from scilpy.io.streamlines import load_tractogram_with_reference, \
    save_tractogram
from scilpy.io.utils import (add_json_args,
                             add_overwrite_arg,
                             add_reference_arg,
                             add_verbose_arg,
                             assert_inputs_exist,
                             assert_outputs_exist, ranged_type)
from scilpy.tractograms.streamline_operations import \
    filter_streamlines_by_length
from scilpy.version import version_string


def _build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter,
                                epilog=version_string)

    p.add_argument('in_tractogram',
                   help='Streamlines input file name.')
    p.add_argument('out_tractogram',
                   help='Streamlines output file name.')
    p.add_argument('--minL', default=0., type=ranged_type(float, 0, None),
                   help='Minimum length of streamlines, in mm. [%(default)s]')
    p.add_argument('--maxL', default=np.inf, type=ranged_type(float, 0, None),
                   help='Maximum length of streamlines, in mm. [%(default)s]')
    p.add_argument('--no_empty', action='store_true',
                   help='Do not write file if there is no streamline.')
    p.add_argument('--display_counts', action='store_true',
                   help='Print streamline count before and after filtering')
    p.add_argument('--out_rejected',
                   help='If specified, save rejected streamlines to this '
                   'file.')
    add_json_args(p)
    add_reference_arg(p)
    add_verbose_arg(p)
    add_overwrite_arg(p)

    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    # Verifications
    assert_inputs_exist(parser, args.in_tractogram, args.reference)
    assert_outputs_exist(parser, args, args.out_tractogram)

    if args.minL == 0 and np.isinf(args.maxL):
        logging.info("You have not specified minL nor maxL. Output will "
                     "simply be a copy of your input!")

    # Loading
    sft = load_tractogram_with_reference(parser, args, args.in_tractogram)

    # Processing
    return_rejected = args.out_rejected is not None

    # Returns (new_sft, _, [rejected_sft]) in filtered_result
    filtered_result = filter_streamlines_by_length(
        sft, args.minL, args.maxL, return_rejected=return_rejected)

    new_sft = filtered_result[0]

    if return_rejected:
        rejected_sft = filtered_result[2]
        save_tractogram(rejected_sft, args.out_rejected, args.no_empty)

    if args.display_counts:
        sc_bf = len(sft.streamlines)
        sc_af = len(new_sft.streamlines)
        print(json.dumps({'streamline_count_before_filtering': int(sc_bf),
                         'streamline_count_after_filtering': int(sc_af)},
                         indent=args.indent))

    # Saving
    save_tractogram(new_sft, args.out_tractogram, args.no_empty)


if __name__ == "__main__":
    main()
