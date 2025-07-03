// AWS AI Cost Calculator - Accuracy Checker
// Automatically validates cost calculation results

class AccuracyChecker {
    constructor() {
        this.results = null;
        this.accuracyState = {
            overall: 'pending',
            checks: {},
            issues: [],
            recommendations: []
        };
    }

    // Run all accuracy checks when results are loaded
    async checkAccuracy(costData) {
        console.log('🔍 Running accuracy checks on cost data...', costData);
        this.results = costData;
        
        // Reset state
        this.accuracyState = {
            overall: 'checking',
            checks: {},
            issues: [],
            recommendations: [],
            timestamp: new Date().toISOString()
        };

        // Run all checks
        this.checkServiceCostRatios();
        this.checkProjectAttribution();
        this.checkCostMagnitude();
        this.checkResourceDiscovery();
        this.checkDateRange();
        
        // Determine overall accuracy
        this.determineOverallAccuracy();
        
        // Display results
        this.displayAccuracyBadge();
        
        // Store for debugging
        window.accuracyState = this.accuracyState;
        
        return this.accuracyState;
    }

    // Check 1: Service cost ratios make sense
    checkServiceCostRatios() {
        const check = {
            name: 'Service Cost Ratios',
            passed: true,
            details: []
        };

        let services = {};
        let totalCost = 0;

        // Handle detailed report format
        if (this.results.service_breakdown) {
            services = this.results.service_breakdown;
            // Calculate total
            Object.values(services).forEach(service => {
                totalCost += service.total_cost || 0;
            });
        } 
        // Handle simple cost format - aggregate from accounts
        else if (this.results.costs_by_account) {
            // Aggregate service costs across all accounts
            this.results.costs_by_account.forEach(account => {
                Object.entries(account.services || {}).forEach(([service, cost]) => {
                    if (!services[service]) {
                        services[service] = { total_cost: 0 };
                    }
                    services[service].total_cost += cost;
                    totalCost += cost;
                });
            });
        }

        // Check ratios if we have service data
        if (Object.keys(services).length > 0 && totalCost > 0) {
            Object.entries(services).forEach(([serviceName, data]) => {
                const cost = data.total_cost || data;
                const ratio = (cost / totalCost) * 100;
                
                // Unusual ratios - but Kendra is expected to be expensive
                if (ratio > 90) {
                    if (serviceName.toLowerCase() === 'kendra' || serviceName === 'Amazon Kendra') {
                        // Kendra is expected to dominate costs due to its pricing model
                        check.details.push(`${serviceName} is ${ratio.toFixed(1)}% of total - this is expected for Kendra`);
                    } else {
                        check.passed = false;
                        check.details.push(`${serviceName} is ${ratio.toFixed(1)}% of total - unusually high`);
                        this.accuracyState.issues.push({
                            type: 'warning',
                            message: `${serviceName} dominates costs at ${ratio.toFixed(1)}%`
                        });
                    }
                }
            });
        } else {
            check.details.push('No service breakdown available');
        }

        this.accuracyState.checks.serviceCostRatios = check;
    }

    // Check 2: Project attribution completeness
    checkProjectAttribution() {
        const check = {
            name: 'Project Attribution',
            passed: true,
            details: []
        };

        let projects = {};
        let totalAttributed = 0;
        let unattributedCost = 0;

        // Handle detailed report format
        if (this.results.project_breakdown) {
            projects = this.results.project_breakdown;
            Object.entries(projects).forEach(([project, data]) => {
                const cost = data.total_cost || 0;
                if (project === 'unattributed' || project === 'Unknown') {
                    unattributedCost += cost;
                } else {
                    totalAttributed += cost;
                }
            });
        }
        // Handle simple cost format - aggregate from accounts
        else if (this.results.costs_by_account) {
            this.results.costs_by_account.forEach(account => {
                Object.entries(account.projects || {}).forEach(([project, cost]) => {
                    if (project === 'unattributed' || project === 'Unknown') {
                        unattributedCost += cost;
                    } else {
                        totalAttributed += cost;
                    }
                });
            });
        }

        if (totalAttributed > 0 || unattributedCost > 0) {
            const unattributedRatio = (unattributedCost / (totalAttributed + unattributedCost)) * 100;

            if (unattributedRatio > 50) {
                check.passed = false;
                check.details.push(`${unattributedRatio.toFixed(1)}% of costs are unattributed`);
                this.accuracyState.recommendations.push({
                    type: 'tagging',
                    message: 'Improve resource tagging to reduce unattributed costs'
                });
            } else if (unattributedRatio > 0) {
                check.details.push(`${unattributedRatio.toFixed(1)}% of costs are unattributed`);
            }
        } else {
            check.details.push('No project attribution data available');
        }

        this.accuracyState.checks.projectAttribution = check;
    }

    // Check 3: Cost magnitude sanity check
    checkCostMagnitude() {
        const check = {
            name: 'Cost Magnitude',
            passed: true,
            details: []
        };

        // Handle both detailed report format and simple cost format
        const totalCost = this.results.organization_summary?.total_ai_spend || 
                         this.results.grand_total || 0;
        
        // Get resource count for context
        const resourceCount = this.results.total_resources || 
                            (window.discoveryData ? window.discoveryData.reduce((sum, d) => sum + (d.summary?.total_ai_resources || 0), 0) : 0);
        
        // Sanity checks
        if (totalCost > 100000) {
            check.details.push('Very high costs detected - verify date range');
            this.accuracyState.issues.push({
                type: 'warning',
                message: 'Costs exceed $100k - verify this is expected'
            });
        }

        if (totalCost === 0) {
            // Check if we have resources but no costs
            if (resourceCount > 0) {
                check.passed = true; // Don't fail if resources exist
                check.details.push(`No costs found for ${resourceCount} resources - possible reasons:`);
                check.details.push('• Resources may not have incurred costs in selected date range');
                check.details.push('• Resources may be in free tier');
                check.details.push('• Cost data may take 24-48 hours to appear');
                this.accuracyState.recommendations.push({
                    type: 'costs',
                    message: 'Try a longer date range or wait for cost data to be available'
                });
            } else {
                check.passed = false;
                check.details.push('No costs found and no resources discovered');
                this.accuracyState.issues.push({
                    type: 'error',
                    message: 'No AI costs or resources detected'
                });
            }
        } else {
            check.details.push(`Total AI costs: $${totalCost.toFixed(2)}`);
        }

        this.accuracyState.checks.costMagnitude = check;
    }

    // Check 4: Resource discovery validation
    checkResourceDiscovery() {
        const check = {
            name: 'Resource Discovery',
            passed: true,
            details: []
        };

        // Handle both detailed report format and check global discoveryData
        let resourceCount = this.results.organization_summary?.total_resources || 
                           this.results.total_resources || 0;
        
        // If not in results, try to get from global discoveryData
        if (resourceCount === 0 && window.discoveryData) {
            resourceCount = window.discoveryData.reduce((sum, d) => {
                return sum + (d.summary?.total_ai_resources || 0);
            }, 0);
        }
        
        if (resourceCount === 0) {
            check.passed = false;
            check.details.push('No AI resources discovered');
            this.accuracyState.issues.push({
                type: 'error',
                message: 'No AI resources found - check permissions'
            });
        } else if (resourceCount < 5) {
            check.details.push(`Found ${resourceCount} AI resources - might be incomplete`);
            this.accuracyState.recommendations.push({
                type: 'discovery',
                message: 'Few resources found - verify all AI services are included'
            });
        } else {
            check.details.push(`Successfully discovered ${resourceCount} AI resources`);
            // Add service breakdown if available
            if (window.discoveryData && window.discoveryData[0]?.services) {
                const services = Object.keys(window.discoveryData[0].services);
                check.details.push(`Services found: ${services.join(', ')}`);
            }
        }

        this.accuracyState.checks.resourceDiscovery = check;
    }

    // Check 5: Date range validation
    checkDateRange() {
        const check = {
            name: 'Date Range',
            passed: true,
            details: []
        };

        // Check if date range is reasonable
        const dateRange = this.results.date_range;
        let start, end, days;
        
        if (dateRange) {
            // Handle detailed report format
            start = new Date(dateRange.start);
            end = new Date(dateRange.end);
        } else if (this.results.period) {
            // Handle simple format "2025-06-01 to 2025-06-30"
            const periodMatch = this.results.period.match(/(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})/);
            if (periodMatch) {
                start = new Date(periodMatch[1]);
                end = new Date(periodMatch[2]);
            }
        } else if (window.selectedDates) {
            // Check global selectedDates
            start = new Date(window.selectedDates.startDate);
            end = new Date(window.selectedDates.endDate);
        }
        
        if (start && end) {
            days = (end - start) / (1000 * 60 * 60 * 24) + 1;
            check.details.push(`Analyzed ${days} days of data`);

            if (days < 7) {
                check.details.push('Short date range - costs may be incomplete');
                this.accuracyState.recommendations.push({
                    type: 'dateRange',
                    message: 'Use at least 30 days for more accurate cost analysis'
                });
            }
        } else {
            check.details.push('Date range information not available');
        }

        this.accuracyState.checks.dateRange = check;
    }

    // Determine overall accuracy state
    determineOverallAccuracy() {
        const checks = Object.values(this.accuracyState.checks);
        const passedChecks = checks.filter(c => c.passed).length;
        const totalChecks = checks.length;

        if (passedChecks === totalChecks) {
            this.accuracyState.overall = 'accurate';
        } else if (passedChecks >= totalChecks * 0.6) {
            this.accuracyState.overall = 'mostly_accurate';
        } else {
            this.accuracyState.overall = 'needs_review';
        }

        // Add summary
        this.accuracyState.summary = {
            passedChecks,
            totalChecks,
            accuracy: ((passedChecks / totalChecks) * 100).toFixed(0) + '%'
        };
    }

    // Display accuracy badge in UI
    displayAccuracyBadge() {
        // Create or update accuracy indicator
        let badge = document.getElementById('accuracy-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'accuracy-badge';
            badge.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                cursor: pointer;
                z-index: 1000;
            `;
            document.body.appendChild(badge);
        }

        // Set badge color and text based on accuracy
        const states = {
            accurate: { 
                color: '#10b981', 
                bg: '#d1fae5', 
                text: '✅ Accurate',
                detail: 'All checks passed'
            },
            mostly_accurate: { 
                color: '#f59e0b', 
                bg: '#fef3c7', 
                text: '⚠️ Mostly Accurate',
                detail: `${this.accuracyState.summary.accuracy} accuracy`
            },
            needs_review: { 
                color: '#ef4444', 
                bg: '#fee2e2', 
                text: '❌ Needs Review',
                detail: 'Multiple issues found'
            },
            checking: { 
                color: '#3b82f6', 
                bg: '#dbeafe', 
                text: '🔍 Checking...',
                detail: 'Running validation'
            }
        };

        const state = states[this.accuracyState.overall] || states.checking;
        badge.style.backgroundColor = state.bg;
        badge.style.color = state.color;
        badge.innerHTML = `
            <div>${state.text}</div>
            <div style="font-size: 12px; font-weight: normal;">${state.detail}</div>
        `;

        // Add click handler to show details
        badge.onclick = () => this.showAccuracyDetails();

        // Auto-hide after 10 seconds if accurate
        if (this.accuracyState.overall === 'accurate') {
            setTimeout(() => {
                badge.style.opacity = '0.7';
            }, 10000);
        }
    }

    // Show detailed accuracy report
    showAccuracyDetails() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        `;

        let html = '<h2>Accuracy Check Results</h2>';
        html += `<p>Overall Accuracy: <strong>${this.accuracyState.summary.accuracy}</strong></p>`;

        // Show checks
        html += '<h3>Validation Checks:</h3>';
        html += '<ul>';
        Object.entries(this.accuracyState.checks).forEach(([key, check]) => {
            const icon = check.passed ? '✅' : '❌';
            html += `<li>${icon} <strong>${check.name}</strong>`;
            if (check.details.length > 0) {
                html += '<ul>';
                check.details.forEach(detail => {
                    html += `<li>${detail}</li>`;
                });
                html += '</ul>';
            }
            html += '</li>';
        });
        html += '</ul>';

        // Show issues
        if (this.accuracyState.issues.length > 0) {
            html += '<h3>Issues Found:</h3>';
            html += '<ul>';
            this.accuracyState.issues.forEach(issue => {
                const icon = issue.type === 'error' ? '❌' : '⚠️';
                html += `<li>${icon} ${issue.message}</li>`;
            });
            html += '</ul>';
        }

        // Show recommendations
        if (this.accuracyState.recommendations.length > 0) {
            html += '<h3>Recommendations:</h3>';
            html += '<ul>';
            this.accuracyState.recommendations.forEach(rec => {
                html += `<li>💡 ${rec.message}</li>`;
            });
            html += '</ul>';
        }

        html += '<button onclick="this.parentElement.parentElement.remove()">Close</button>';

        content.innerHTML = html;
        modal.appendChild(content);
        document.body.appendChild(modal);

        // Close on background click
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };
    }
}

// Initialize accuracy checker
window.accuracyChecker = new AccuracyChecker();

// Auto-run when results are loaded
document.addEventListener('DOMContentLoaded', () => {
    // Intercept result display
    const originalDisplayResults = window.displayResults;
    if (originalDisplayResults) {
        window.displayResults = function(data) {
            // Call original function
            originalDisplayResults(data);
            
            // Run accuracy check
            window.accuracyChecker.checkAccuracy(data);
        };
    }
});

console.log('✅ Accuracy checker loaded. Results will be validated automatically.');