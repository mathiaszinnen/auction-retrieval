from ultralytics import YOLO
from glob import glob
import shutil

class ArtworkDetector:
    def __init__(self, weights_path, input_dir, output_dir, device='cuda:0'):
        self.model = YOLO(weights_path)
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.device = device

    def _batch(self, iterable, n=1):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]
    
    def _move_images(self):
        img_pths = glob(f'{self.output_dir}/predict*/crops/Image/*.jpg')
        for pth in img_pths:
            try:
                shutil.move(pth, self.output_dir)
            except shutil.Error as e:
                print(e)
                continue # ignore if file already exists
        tmpdirs = glob(f'{self.output_dir}/predict*')
        for tmpdir in tmpdirs:
            shutil.rmtree(tmpdir)


    def detect_and_crop(self, chunksize=50):
        self.model.to(self.device)
        imgs = glob(f'{self.input_dir}/*.jpg') + glob(f'{self.input_dir}/*.jpeg')
        print(f'Loaded {len(imgs)} images from {self.input_dir}')
        
        n_chunks = len(imgs) // chunksize + (len(imgs) % chunksize > 0)
        for i, img_chunk in enumerate(self._batch(imgs, chunksize), 1):
            print(f'Predicting for chunk {i}/{n_chunks}...')
            self.model.predict(img_chunk, save_crop=True, device=self.device, project=self.output_dir)
            self._move_images()
        
        print('Predictions complete!')
