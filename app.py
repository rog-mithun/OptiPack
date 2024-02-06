from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import copy
import random
app = Flask(__name__)


class Shipment:
    def __init__(self, name, length, height, width, weight, quantity, rotation_type = 'any'):
        self.name = name
        self.length = length
        self.height = height
        self.width = width
        self.weight = weight
        self.quantity = quantity
        self.rotation_type = rotation_type


class Bin:
    def __init__(self, name, length, height, width, max_weight, quantity):
        self.name = name
        self.length = length
        self.height = height
        self.width = width
        self.max_weight = max_weight
        self.quantity = quantity
        self.current_weight = 0
        self.items = []


def can_shipment_fit(bin, shipment):
    if shipment.rotation_type == 'horizontal':
        return (
            bin.width >= shipment.height
            and bin.length >= shipment.width
            and bin.height >= shipment.length
            and bin.max_weight >= bin.current_weight + shipment.weight
            and bin.quantity > 0
        )
    elif shipment.rotation_type == 'vertical':
        return (
            bin.length >= shipment.length
            and bin.width >= shipment.width
            and bin.height >= shipment.height
            and bin.max_weight >= bin.current_weight + shipment.weight
            and bin.quantity > 0
        )
    elif shipment.rotation_type == 'any':
        # Consider any rotation type
        return (
            bin.width >= shipment.height
            and bin.length >= shipment.width
            and bin.height >= shipment.length
            and bin.max_weight >= bin.current_weight + shipment.weight
            and bin.quantity > 0
        )
    else:
        # Invalid rotation type
        return False





def pack_shipments(shipments, bins):
    # Sort shipments by total volume in descending order
    shipments.sort(key=lambda x: x.length * x.width * x.height, reverse=True)

    unfitted_items = []

    for shipment in shipments:
        placed = False
        for bin in bins:
            # Check if the item is already placed in the bin
            if any(item.name == shipment.name and item.quantity > 0 for item in bin.items):
                continue

            remaining_quantity = shipment.quantity
            for item in bin.items:
                if item.name == shipment.name:
                    # Deduct the quantity of the item already present in the bin
                    remaining_quantity -= max(item.quantity, 0)

            while can_shipment_fit(bin, shipment) and remaining_quantity > 0:
                # Create a new item instance to place in the bin
                quantity_to_place = min(remaining_quantity, 1)
                item_to_place = Shipment(
                    shipment.name, shipment.length, shipment.height,
                    shipment.width, shipment.weight, quantity_to_place,
                    rotation_type=shipment.rotation_type
                )
                bin.items.append(item_to_place)
                bin.current_weight += item_to_place.weight
                remaining_quantity -= quantity_to_place
                shipment.quantity -= quantity_to_place
                print(f"Item {shipment.name} placed in bin: {bin.name} (Quantity: {item_to_place.quantity})")
                placed = True

                # Trigger animation for each placement
                yield bins

        if not placed and shipment.quantity > 0:
            # If no bin can accommodate the remaining quantity of the shipment, add it to the unfitted items list
            unfitted_items.append({'name': shipment.name, 'quantity': shipment.quantity})

    return unfitted_items
   





def visualize_solution(bins):
    fig = plt.figure(figsize=(12, 8))
    sliders = []

    for i, bin in enumerate(bins):
        if not bin.items:
            continue  # Skip bins without items

        ax = fig.add_subplot(1, len(bins), i + 1, projection='3d', adjustable='box')

        item_colors = {}  # Use a dictionary to store unique colors for each item in the bin

        max_volume = bin.length * bin.width * bin.height  # Calculate the maximum volume of the bin
        total_volume = sum(item.length * item.width * item.height for item in bin.items)  # Calculate total volume based on items in the bin
        filled_percentage = (total_volume / max_volume) * 100  # Calculate filled percentage based on volume

        current_position_length = 0  # Initialize the current position within the bin
        current_position_width = 0
        # Plot the bin with its dimensions
        ax.bar3d(
            0, 0, 0,
            bin.length, bin.width, bin.height,  # Set dx, dy, dz to the dimensions of the bin
            color='lightgray',
            alpha=0
        )

        for j, item in enumerate(bin.items):
            item_color = plt.cm.viridis(j / len(bin.items))  # Use different colors for each item in the bin

            if item.rotation_type == 'horizontal':
                ax.bar3d(
                    current_position_length,
                    current_position_width,
                    0,
                    item.width,
                    item.height,
                    item.length,
                    color=item_color,
                    shade=True
                )
                current_position_length += item.width
            elif item.rotation_type == 'vertical':
                ax.bar3d(
                    current_position_length,
                    current_position_width,
                    0,
                    item.length,
                    item.width,
                    item.height,
                    color=item_color,
                    shade=True
                )
                current_position_length += item.length

            elif item.rotation_type == 'any':
                ax.bar3d(
                    current_position_length,
                    current_position_width,
                    0,
                    item.width,
                    item.height,
                    item.length,
                    color=item_color,
                    shade=True
                )
                current_position_length += item.width

            else:
                return False 

            item_colors[item.name] = item_colors.get(item.name, []) + [item_color]

        ax.set_xlabel('Length')
        ax.set_ylabel('Width')
        ax.set_zlabel('Height')
        ax.set_title(f'{bin.name} - {filled_percentage:.2f}% filled')

        # Create legend for items in the bin, considering quantity
        legend_items = []
        for item_name, colors in item_colors.items():
            for idx, color in enumerate(colors, start=1):
                label = f"{item_name} ({idx})"
                legend_items.append(plt.Rectangle((0, 0), 1, 1, color=color, label=label))

        ax.legend(handles=legend_items, loc='upper left', bbox_to_anchor=(1, 1))

        # Add slider for each bin below the respective bin with smaller size
        slider_x_position = ax.get_position().x0 - 0.1 + i * 0.2 / len(bins)
        ax_slider = plt.axes([slider_x_position, ax.get_position().y0 - 0.1, ax.get_position().width, 0.02],
                             facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'', 0, 360, valinit=0)
        def update(val, ax=ax, sliders=sliders):
                ax.view_init(azim=val)
                for s in sliders:
                    if s.ax != ax:
                        s.valtext.set_text(f'{s.label.get_text()}: {s.val:.2f}')
                fig.canvas.draw_idle()

        slider.on_changed(update)
        sliders.append(slider)

    fig.suptitle('3D Visualization of Bin Packing', fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()




def visualize_empty_bins(bins):
    fig = plt.figure(figsize=(12, 8))
    sliders = []

    for i, bin in enumerate(bins):
        ax = fig.add_subplot(1, len(bins), i + 1, projection='3d', adjustable='box')
        ax.set_xlabel('Length')
        ax.set_ylabel('Width')
        ax.set_zlabel('Height')
        ax.set_title(f'{bin.name}')

        slider_x_position = ax.get_position().x0 - 0.1 + i * 0.2 / len(bins)
        ax_slider = plt.axes([slider_x_position, ax.get_position().y0 - 0.1, ax.get_position().width, 0.02],
                             facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'', 0, 360, valinit=0)
        sliders.append(slider)

        def update(val, ax=ax):
            ax.view_init(elev=20, azim=val)
            fig.canvas.draw_idle()

        slider.on_changed(update)
        sliders.append(slider)

    fig.suptitle('3D Visualization of Bin Packing', fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

def pack_shipments_with_animation(shipments, bins):
    # Create a copy of the bins to visualize empty bins
    empty_bins = copy.deepcopy(bins)
    visualize_empty_bins(empty_bins)
    plt.show()

    # Animation for bin packing
    fig = plt.figure(figsize=(12, 8))
    animation = FuncAnimation(fig, visualize_solution, frames=pack_shipments(shipments, bins), interval=1000, repeat=False)
    plt.show()


@app.route('/api/pack_shipments', methods=['POST'])
def api_pack_shipments():
    try:
        data = request.json
        shipments = [Shipment(**item) for item in data.get('shipments', [])]
        bins = [Bin(**item) for item in data.get('bins', [])]

        # Use FuncAnimation for animation with initial visualization of empty bins
        pack_shipments_with_animation(shipments, bins)

        result = {'bins': []}
        unfitted_items = []

        for bin in bins:
            bin_result = {
                'name': bin.name,
                'current_weight': bin.current_weight,
                'max_weight': bin.max_weight,
                'quantity': bin.quantity,
                'items': []
            }

            for item in bin.items:
                item_info = {
                    'name': item.name,
                    'quantity': item.quantity,
                    'rotation_type': item.rotation_type  # Include rotation type in the result
                }
                bin_result['items'].append(item_info)

            result['bins'].append(bin_result)

        # Collect unfitted items
        unfitted_items.extend([{'name': shipment.name, 'quantity': shipment.quantity} for shipment in shipments if shipment.quantity > 0])

        # Include unfitted items in the response
        if unfitted_items:
            result['unfitted_items'] = unfitted_items

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5012)