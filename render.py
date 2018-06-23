# Simple script to render cadquery models via the cqgi interface
# Usage: render.py mymodel.py path/to/output.gltf

from cadquery import cqgi
import argparse
import sys
import os

parser = argparse.ArgumentParser(description="Utility to render cqparts models to gltf. Each model in a given file is rendered to a separate gltf.")
parser.add_argument('--file', required=True, help="cqparts python file to render models from")
parser.add_argument('--out_dir', required=True, help="Output directory")
args = parser.parse_args()

fname = args.file

with open(fname, 'r') as f:
    build_result = cqgi.parse(f.read()).build()

print("Build results: %s" % str(build_result.results))

out_basedir = args.out_dir

for res in build_result.results:
    asm = res.shape
    clsname = asm.__class__.__name__
    outdir = os.path.join(out_basedir, clsname)
    os.mkdir(outdir)

    outfile = os.path.join(outdir, clsname + '.gltf')

    print("Writing '%s' object to '%s'" % ( clsname, outfile))

    asm.exporter('gltf')(outfile)
