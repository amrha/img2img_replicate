import torch
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor, Resize
import requests
from PIL import Image
from io import BytesIO
from diffusers import StableDiffusionImg2ImgPipeline, LMSDiscreteScheduler
import os
from urllib.parse import urlparse

def initialize_pipeline(pipeline_model="nitrosocke/Ghibli-Diffusion", device="cpu"):
    """
    Initializes a diffusion-based image-to-image pipeline with a specified model and device.

    Args:
        pipeline_model (str, optional): The identifier of the pretrained model to load. Defaults to "nitrosocke/Ghibli-Diffusion".
        device (str, optional): The type of device to run the model on. Should be either "cuda" or "cpu". Defaults to "cuda".

    Returns:
        pipe: An instance of StableDiffusionImg2ImgPipeline loaded with the pretrained model and set to run on the specified device.
    """
    # Initialize pipeline
    dtype = torch.float32
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(pipeline_model, safety_checker = None,
                                                          torch_dtype=dtype).to(device)
    # Update scheduler
    lms = LMSDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.scheduler = lms

    return pipe

def generate_image(pipe, device="cpu", url_or_filepath="assets/sketch-mountains-input.jpg", prompt="A painting in the style of van gogh.",
                   strength=0.75, guidance_scale=7.5, seed=1024):
    """
    Generates a new image based on an initial image and a textual prompt.

    Args:
        pipe: The initialized image-to-image pipeline to generate images with.
        device (str, optional): The type of device to run the model on. Should be either "cuda" or "cpu". Defaults to "cuda".
        url_or_filepath (str, optional): The URL or local filepath of the initial image. This must be provided.
        prompt (str, optional): The textual prompt to guide the image generation. This must be provided.
        strength (float, optional): The strength of the guidance prompt. Defaults to 0.75.
        guidance_scale (float, optional): The scale of the guidance. Defaults to 7.5.
        seed (int, optional): The seed for the random generator. Defaults to 1024.

    Returns:
        image: The generated image as a tensor.

    Raises:
        ValueError: If either 'url_or_filepath' or 'prompt' is not provided.
    """

    if url_or_filepath is None or prompt is None:
        raise ValueError("Both 'url_or_filepath' and 'prompt' must be provided.")

    # Parse image from url or local file
    parsed = urlparse(url_or_filepath)
    if parsed.scheme in ['http', 'https']:
        # Fetch image from url
        response = requests.get(url_or_filepath)
        init_image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        # Open image from local file
        init_image = Image.open(url_or_filepath).convert("RGB")

    init_image.thumbnail((768, 768))

    # Set up random generator
    generator = torch.Generator(device=device).manual_seed(seed)

    # Generate initial image
    image = pipe(prompt=prompt, image=init_image, strength=strength,
                 guidance_scale=guidance_scale, generator=generator, num_inference_steps=5).images[0]

    return image

if __name__ == '__main__':
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = initialize_pipeline(pipeline_model="nitrosocke/Ghibli-Diffusion", device=device)
    image = generate_image(pipe, device=device, url_or_filepath="assets/sketch-mountains-input.jpg", prompt="A painting in the style of van gogh.")
    image.save("assets/output.png")

