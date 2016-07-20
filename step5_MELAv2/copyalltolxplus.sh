cd $(mktemp -d) &&
pwd &&
for a in nominal scaleup scaledown tuneup tunedown; do
    ln -s $(cd -)/$a/{Djet_,}${a}.{png,eps,root,pdf} . || exit 1
done &&
rsync -zLv --progress * hroskes@lxplus.cern.ch:www/TEST/
