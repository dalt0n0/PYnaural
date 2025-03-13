from PIL import Image, ImageDraw

def create_icon():
    # Create images for different sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        # Create a new image with a white background
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Calculate dimensions
        width, height = size
        padding = width // 8
        center = width // 2
        radius = (width - padding * 2) // 2
        
        # Draw a gradient circle
        for r in range(radius, 0, -1):
            # Create a blue-purple gradient
            intensity = int(255 * (r / radius))
            color = (intensity, 0, 255 - intensity // 2, 255)
            draw.ellipse([center - r, center - r, center + r, center + r], fill=color)
        
        # Add inner circle
        inner_radius = radius // 3
        draw.ellipse([center - inner_radius, center - inner_radius, 
                     center + inner_radius, center + inner_radius], 
                     fill=(255, 255, 255, 255))
        
        images.append(image)
    
    # Save as ICO file with multiple sizes
    images[0].save('app_icon.ico', format='ICO', sizes=[(x, x) for x, _ in sizes],
                  append_images=images[1:])

if __name__ == '__main__':
    create_icon() 