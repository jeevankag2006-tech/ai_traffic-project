import cv2
import numpy as np
from ultralytics import YOLO
import os
import json
from datetime import datetime
import time

class TrafficAnalyzer:
    def __init__(self):
        # Load YOLOv8 model
        self.model = YOLO('yolov8n.pt')
        
        # Vehicle classes in COCO dataset
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle', 
            5: 'bus',
            7: 'truck'
        }
        
        # Traffic density thresholds
        self.density_thresholds = {
            'low': 5,
            'medium': 15,
            'high': 25
        }
        
    def detect_vehicles(self, frame):
        """Detect vehicles in a frame using YOLO"""
        results = self.model(frame, verbose=False)
        vehicles = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                if cls in self.vehicle_classes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    
                    vehicle = {
                        'class': self.vehicle_classes[cls],
                        'confidence': conf,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                    }
                    vehicles.append(vehicle)
        
        return vehicles
    
    def calculate_traffic_density(self, vehicle_count):
        """Calculate traffic density based on vehicle count"""
        if vehicle_count <= self.density_thresholds['low']:
            return 'Low'
        elif vehicle_count <= self.density_thresholds['medium']:
            return 'Medium'
        else:
            return 'High'
    
    def analyze_video(self, video_path):
        """Analyze traffic in video file"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # Analysis results
        results = {
            'video_info': {
                'path': video_path,
                'fps': fps,
                'total_frames': total_frames,
                'duration': duration,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'traffic_analysis': {
                'total_vehicles_detected': 0,
                'vehicle_types': {},
                'peak_density': 'Low',
                'average_vehicles_per_frame': 0,
                'density_timeline': []
            },
            'frame_analysis': []
        }
        
        frame_count = 0
        total_vehicles = 0
        vehicle_type_counts = {v: 0 for v in self.vehicle_classes.values()}
        
        # Process every 30th frame for efficiency
        frame_interval = 30
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                vehicles = self.detect_vehicles(frame)
                vehicle_count = len(vehicles)
                
                # Update vehicle counts
                total_vehicles += vehicle_count
                for vehicle in vehicles:
                    vehicle_type_counts[vehicle['class']] += 1
                
                # Calculate density
                density = self.calculate_traffic_density(vehicle_count)
                
                # Store frame analysis
                frame_data = {
                    'frame_number': frame_count,
                    'timestamp': frame_count / fps,
                    'vehicle_count': vehicle_count,
                    'density': density,
                    'vehicles': vehicles[:10]  # Store first 10 vehicles for demo
                }
                results['frame_analysis'].append(frame_data)
                
                # Update density timeline
                density_data = {
                    'time': frame_count / fps,
                    'vehicle_count': vehicle_count,
                    'density': density
                }
                results['traffic_analysis']['density_timeline'].append(density_data)
            
            frame_count += 1
            
            # Progress update (optional)
            if frame_count % 100 == 0:
                print(f"Processed {frame_count}/{total_frames} frames")
        
        cap.release()
        
        # Calculate final statistics
        analyzed_frames = len(results['frame_analysis'])
        if analyzed_frames > 0:
            results['traffic_analysis']['total_vehicles_detected'] = total_vehicles
            results['traffic_analysis']['vehicle_types'] = vehicle_type_counts
            results['traffic_analysis']['average_vehicles_per_frame'] = total_vehicles / analyzed_frames
            
            # Find peak density
            density_counts = {'Low': 0, 'Medium': 0, 'High': 0}
            for frame_data in results['frame_analysis']:
                density_counts[frame_data['density']] += 1
            
            peak_density = max(density_counts, key=density_counts.get)
            results['traffic_analysis']['peak_density'] = peak_density
        
        # Generate recommendations
        results['recommendations'] = self.generate_recommendations(results)
        
        return results
    
    def generate_recommendations(self, analysis_results):
        """Generate traffic management recommendations"""
        recommendations = []
        
        avg_vehicles = analysis_results['traffic_analysis']['average_vehicles_per_frame']
        peak_density = analysis_results['traffic_analysis']['peak_density']
        vehicle_types = analysis_results['traffic_analysis']['vehicle_types']
        
        # Density-based recommendations
        if peak_density == 'High':
            recommendations.append({
                'type': 'signal_timing',
                'message': 'Consider extending green light duration during peak hours',
                'priority': 'High'
            })
            recommendations.append({
                'type': 'traffic_flow',
                'message': 'Implement dynamic lane allocation to manage congestion',
                'priority': 'Medium'
            })
        
        # Vehicle type-based recommendations
        total_vehicles = sum(vehicle_types.values())
        if total_vehicles > 0:
            truck_percentage = (vehicle_types['truck'] / total_vehicles) * 100
            if truck_percentage > 20:
                recommendations.append({
                    'type': 'heavy_vehicle',
                    'message': 'High percentage of heavy vehicles detected - consider dedicated truck lanes',
                    'priority': 'Medium'
                })
        
        # General recommendations
        if avg_vehicles < 5:
            recommendations.append({
                'type': 'optimization',
                'message': 'Low traffic density - consider reducing signal cycle time',
                'priority': 'Low'
            })
        
        return recommendations
    
    def get_real_time_analysis(self, frame):
        """Get real-time traffic analysis for a single frame"""
        vehicles = self.detect_vehicles(frame)
        vehicle_count = len(vehicles)
        density = self.calculate_traffic_density(vehicle_count)
        
        return {
            'vehicle_count': vehicle_count,
            'density': density,
            'vehicles': vehicles[:5],  # Return first 5 vehicles
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    
    def export_results(self, results, output_path):
        """Export analysis results to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Analysis results exported to: {output_path}")

# Utility function for testing
def test_analyzer():
    """Test the traffic analyzer with sample data"""
    analyzer = TrafficAnalyzer()
    
    # Create a test frame (black image)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test vehicle detection
    vehicles = analyzer.detect_vehicles(test_frame)
    print(f"Test detection found {len(vehicles)} vehicles")
    
    # Test density calculation
    density = analyzer.calculate_traffic_density(10)
    print(f"Test density: {density}")

if __name__ == "__main__":
    test_analyzer()
