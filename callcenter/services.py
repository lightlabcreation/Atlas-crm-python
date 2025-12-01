# callcenter/services.py
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import OrderAssignment, AgentSession
from orders.models import Order
from roles.models import Role, UserRole
import math
from datetime import datetime, timedelta

User = get_user_model()

class OrderDistributionService:
    """Service for automatically distributing orders among call center agents."""
    
    @staticmethod
    def get_available_agents():
        """Get all available call center agents."""
        call_center_role = Role.objects.filter(name='Call Center Agent').first()
        if not call_center_role:
            return User.objects.none()
        
        return User.objects.filter(
            user_roles__role=call_center_role,
            user_roles__is_active=True
        ).distinct()
    
    @staticmethod
    def get_agent_workload(agent):
        """Get current workload for an agent (number of active assignments)."""
        today = timezone.now().date()
        return OrderAssignment.objects.filter(
            agent=agent,
            assignment_date__date=today,
            order__status__in=['pending', 'processing', 'confirmed']
        ).count()
    
    @staticmethod
    def get_agent_performance_score(agent):
        """Calculate performance score for an agent based on recent performance."""
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        
        # Get recent performance data
        recent_assignments = OrderAssignment.objects.filter(
            agent=agent,
            assignment_date__date__gte=yesterday
        )
        
        if not recent_assignments.exists():
            return 1.0  # Default score for new agents
        
        # Calculate success rate
        total_orders = recent_assignments.count()
        successful_orders = recent_assignments.filter(
            order__status='confirmed'
        ).count()
        
        success_rate = successful_orders / total_orders if total_orders > 0 else 0.5
        
        # Calculate average completion time (simplified)
        avg_completion_time = 1.0  # Default value
        
        # Combine factors for final score
        performance_score = (success_rate * 0.7) + (avg_completion_time * 0.3)
        
        return max(0.1, min(2.0, performance_score))  # Clamp between 0.1 and 2.0
    
    @staticmethod
    def distribute_orders_automatically():
        """Automatically distribute unassigned orders among available agents."""
        # Get unassigned orders
        unassigned_orders = Order.objects.filter(
            status__in=['pending', 'processing'],
            assignments__isnull=True
        ).order_by('date')
        
        if not unassigned_orders.exists():
            return {
                'success': True,
                'message': 'No unassigned orders to distribute',
                'distributed_count': 0
            }
        
        # Get available agents
        available_agents = OrderDistributionService.get_available_agents()
        
        if not available_agents.exists():
            return {
                'success': False,
                'message': 'No available call center agents found',
                'distributed_count': 0
            }
        
        # Calculate distribution
        total_orders = unassigned_orders.count()
        total_agents = available_agents.count()
        orders_per_agent = math.ceil(total_orders / total_agents)
        
        # Get current workloads and performance scores
        agent_data = []
        for agent in available_agents:
            workload = OrderDistributionService.get_agent_workload(agent)
            performance_score = OrderDistributionService.get_agent_performance_score(agent)
            
            # Calculate adjusted capacity (higher performance = more capacity)
            adjusted_capacity = max(0, orders_per_agent - workload)
            adjusted_capacity = int(adjusted_capacity * performance_score)
            
            agent_data.append({
                'agent': agent,
                'workload': workload,
                'performance_score': performance_score,
                'adjusted_capacity': adjusted_capacity,
                'assigned_count': 0
            })
        
        # Sort agents by adjusted capacity (descending)
        agent_data.sort(key=lambda x: x['adjusted_capacity'], reverse=True)
        
        # Distribute orders
        distributed_count = 0
        agent_index = 0
        
        for order in unassigned_orders:
            # Find agent with available capacity
            assigned = False
            attempts = 0
            
            while not assigned and attempts < len(agent_data):
                agent_info = agent_data[agent_index]
                
                if agent_info['assigned_count'] < agent_info['adjusted_capacity']:
                    # Assign order to this agent
                    OrderAssignment.objects.create(
                        order=order,
                        manager=User.objects.filter(is_superuser=True).first(),  # System assignment
                        agent=agent_info['agent'],
                        priority_level='medium',
                        manager_notes='Automatically distributed by system',
                        assignment_reason='Automatic distribution'
                    )
                    
                    agent_info['assigned_count'] += 1
                    distributed_count += 1
                    assigned = True
                
                # Move to next agent
                agent_index = (agent_index + 1) % len(agent_data)
                attempts += 1
            
            # If no agent available, assign to first agent
            if not assigned:
                first_agent = agent_data[0]['agent']
                OrderAssignment.objects.create(
                    order=order,
                    manager=User.objects.filter(is_superuser=True).first(),
                    agent=first_agent,
                    priority_level='medium',
                    manager_notes='Automatically distributed by system (fallback)',
                    assignment_reason='Automatic distribution - fallback'
                )
                distributed_count += 1
        
        return {
            'success': True,
            'message': f'Successfully distributed {distributed_count} orders among {total_agents} agents',
            'distributed_count': distributed_count,
            'total_agents': total_agents,
            'orders_per_agent': orders_per_agent
        }
    
    @staticmethod
    def reassign_order(order_id, new_agent_id, manager_id, reason=''):
        """Reassign an order from one agent to another."""
        try:
            order = Order.objects.get(id=order_id)
            new_agent = User.objects.get(id=new_agent_id)
            manager = User.objects.get(id=manager_id)
            
            # Get current assignment
            current_assignment = OrderAssignment.objects.filter(
                order=order,
                agent__isnull=False
            ).first()
            
            if current_assignment:
                # Store previous agent
                previous_agent = current_assignment.agent
                
                # Update assignment
                current_assignment.previous_agent = previous_agent
                current_assignment.agent = new_agent
                current_assignment.manager = manager
                current_assignment.assignment_reason = f'Reassigned by {manager.get_full_name() or manager.username}. {reason}'
                current_assignment.save()
                
                return {
                    'success': True,
                    'message': f'Order reassigned from {previous_agent.get_full_name() or previous_agent.username} to {new_agent.get_full_name() or new_agent.username}',
                    'previous_agent': previous_agent,
                    'new_agent': new_agent
                }
            else:
                # Create new assignment if none exists
                OrderAssignment.objects.create(
                    order=order,
                    manager=manager,
                    agent=new_agent,
                    priority_level='medium',
                    manager_notes=f'Assigned by {manager.get_full_name() or manager.username}',
                    assignment_reason=reason or 'Manual assignment'
                )
                
                return {
                    'success': True,
                    'message': f'Order assigned to {new_agent.get_full_name() or new_agent.username}',
                    'new_agent': new_agent
                }
                
        except (Order.DoesNotExist, User.DoesNotExist) as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_agent_distribution_summary():
        """Get summary of current order distribution among agents."""
        today = timezone.now().date()
        available_agents = OrderDistributionService.get_available_agents()
        
        summary = []
        total_assigned = 0
        
        for agent in available_agents:
            workload = OrderAssignment.objects.filter(
                agent=agent,
                assignment_date__date=today,
                order__status__in=['pending', 'processing', 'confirmed']
            ).count()
            
            performance_score = OrderDistributionService.get_agent_performance_score(agent)
            
            summary.append({
                'agent': agent,
                'agent_name': agent.get_full_name() or agent.username,
                'workload': workload,
                'performance_score': performance_score,
                'status': 'Available' if workload < 10 else 'Busy'
            })
            
            total_assigned += workload
        
        # Get unassigned orders
        unassigned_count = Order.objects.filter(
            status__in=['pending', 'processing'],
            assignments__isnull=True
        ).count()
        
        return {
            'agents': summary,
            'total_assigned': total_assigned,
            'unassigned_count': unassigned_count,
            'total_agents': len(summary)
        } 

class AutoOrderDistributionService:
    """Service for automatically distributing orders to call center agents equally"""
    
    @staticmethod
    def get_available_agents():
        """Get all available call center agents"""
        return User.objects.filter(
            user_roles__role__name='Call Center Agent',
            user_roles__is_active=True
        ).distinct()
    
    @staticmethod
    def get_agent_workload(agent, date=None):
        """Get current workload for an agent"""
        if date is None:
            date = timezone.now().date()
        
        # Count orders assigned today
        today_orders = OrderAssignment.objects.filter(
            agent=agent,
            assignment_date__date=date
        ).count()
        
        return today_orders
    
    @staticmethod
    def distribute_orders_equally():
        """Distribute all unassigned orders equally among available agents"""
        # Get all unassigned orders
        unassigned_orders = Order.objects.filter(
            status__in=['pending', 'pending_confirmation'],
            assignments__isnull=True
        ).order_by('date')
        
        # Get available agents
        available_agents = AutoOrderDistributionService.get_available_agents()
        
        if not available_agents.exists():
            return {
                'success': False,
                'message': 'No available call center agents found',
                'distributed_count': 0
            }
        
        if not unassigned_orders.exists():
            return {
                'success': True,
                'message': 'No unassigned orders to distribute',
                'distributed_count': 0
            }
        
        # Get current workloads for each agent
        agent_workloads = {}
        for agent in available_agents:
            workload = AutoOrderDistributionService.get_agent_workload(agent)
            agent_workloads[agent.id] = {
                'agent': agent,
                'workload': workload,
                'assigned_count': 0
            }
        
        # Sort agents by current workload (ascending)
        sorted_agents = sorted(agent_workloads.values(), key=lambda x: x['workload'])
        
        # Distribute orders equally
        total_orders = unassigned_orders.count()
        total_agents = len(sorted_agents)
        orders_per_agent = total_orders // total_agents
        extra_orders = total_orders % total_agents
        
        distributed_count = 0
        
        # Get first available manager or superuser
        manager = User.objects.filter(
            user_roles__role__name='Call Center Manager'
        ).first()
        
        if not manager:
            manager = User.objects.filter(is_superuser=True).first()
        
        # Distribute orders
        for i, order in enumerate(unassigned_orders):
            # Calculate which agent should get this order
            agent_index = i % total_agents
            agent_info = sorted_agents[agent_index]
            
            # Create assignment
            OrderAssignment.objects.create(
                order=order,
                manager=manager,
                agent=agent_info['agent'],
                priority_level='medium',
                manager_notes='Auto-distributed equally by system',
                assignment_reason='Automatic equal distribution among agents'
            )
            
            # Update workload count
            agent_info['assigned_count'] += 1
            distributed_count += 1
        
        return {
            'success': True,
            'message': f'Successfully distributed {distributed_count} orders equally among {total_agents} agents',
            'distributed_count': distributed_count,
            'total_agents': total_agents,
            'orders_per_agent': orders_per_agent,
            'extra_orders': extra_orders
        }
    
    @staticmethod
    def auto_assign_new_order(order):
        """Automatically assign a new order to the agent with lowest workload"""
        available_agents = AutoOrderDistributionService.get_available_agents()
        
        if not available_agents.exists():
            return False, "No available call center agents found"
        
        # Find agent with lowest workload
        best_agent = None
        lowest_workload = float('inf')
        
        for agent in available_agents:
            workload = AutoOrderDistributionService.get_agent_workload(agent)
            if workload < lowest_workload:
                lowest_workload = workload
                best_agent = agent
        
        if not best_agent:
            return False, "No available agents"
        
        # Get manager
        manager = User.objects.filter(
            user_roles__role__name='Call Center Manager'
        ).first()
        
        if not manager:
            manager = User.objects.filter(is_superuser=True).first()
        
        # Create assignment
        OrderAssignment.objects.create(
            order=order,
            manager=manager,
            agent=best_agent,
            priority_level='medium',
            manager_notes='Auto-assigned to agent with lowest workload',
            assignment_reason='Automatic assignment for new order'
        )
        
        return True, best_agent
    
    @staticmethod
    def balance_workloads():
        """Balance workloads between agents by redistributing orders if needed"""
        available_agents = AutoOrderDistributionService.get_available_agents()
        
        if available_agents.count() < 2:
            return "Need at least 2 agents to balance workloads"
        
        # Get current workloads
        agent_workloads = {}
        for agent in available_agents:
            workload = AutoOrderDistributionService.get_agent_workload(agent)
            agent_workloads[agent.id] = workload
        
        # Find agents with highest and lowest workloads
        max_workload = max(agent_workloads.values())
        min_workload = min(agent_workloads.values())
        
        # If difference is more than 1 order, redistribute
        if max_workload - min_workload > 1:
            # Find overloaded agents
            overloaded_agents = [
                agent_id for agent_id, workload in agent_workloads.items()
                if workload == max_workload
            ]
            
            # Find underloaded agents
            underloaded_agents = [
                agent_id for agent_id, workload in agent_workloads.items()
                if workload == min_workload
            ]
            
            # Redistribute one order from overloaded to underloaded
            for overloaded_id in overloaded_agents:
                if underloaded_agents:
                    # Get one order from overloaded agent
                    order_to_move = OrderAssignment.objects.filter(
                        agent_id=overloaded_id,
                        assignment_date__date=timezone.now().date()
                    ).first()
                    
                    if order_to_move and underloaded_agents:
                        # Move to underloaded agent
                        underloaded_id = underloaded_agents.pop(0)
                        order_to_move.agent_id = underloaded_id
                        order_to_move.assignment_reason = 'Redistributed for workload balance'
                        order_to_move.save()
                        
                        # Update workload counts
                        agent_workloads[overloaded_id] -= 1
                        agent_workloads[underloaded_id] += 1
                        
                        if agent_workloads[overloaded_id] - min(agent_workloads.values()) <= 1:
                            break
            
            return f"Workloads balanced. Max: {max(agent_workloads.values())}, Min: {min(agent_workloads.values())}"
        
        return "Workloads are already balanced" 