for dir in services/*/
do
    cd ${dir} 
    ./build_images.sh
    cd ../../
done
