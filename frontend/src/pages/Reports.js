import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Card,
  CardContent,
  CardActions,
  CircularProgress,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import {
  Assessment as AssessmentIcon,
  GetApp as DownloadIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import axios from 'axios';

function Reports() {
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    dateFrom: null,
    dateTo: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      dateFrom: null,
      dateTo: null,
    });
  };

  const generateJobsReport = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const params = {
        search: filters.search,
        status: filters.status,
        date_from: filters.dateFrom?.toISOString().split('T')[0],
        date_to: filters.dateTo?.toISOString().split('T')[0],
      };

      const response = await axios.get('/api/v1/reports/jobs', {
        params,
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        `jobs_report_${new Date().toISOString().split('T')[0]}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess('Report generated successfully!');
    } catch (error) {
      console.error('Error generating report:', error);
      setError('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Reports
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Jobs Report */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Typography variant="h5">Jobs Report</Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" paragraph>
                Generate a comprehensive report of jobs with detailed statistics and analysis.
                Apply filters to customize the report content.
              </Typography>

              {/* Filters */}
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Search Jobs"
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={filters.status}
                      label="Status"
                      onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                      disabled={loading}
                    >
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="active">Active</MenuItem>
                      <MenuItem value="completed">Completed</MenuItem>
                      <MenuItem value="cancelled">Cancelled</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <DatePicker
                    label="From Date"
                    value={filters.dateFrom}
                    onChange={(date) => setFilters({ ...filters, dateFrom: date })}
                    slotProps={{ textField: { fullWidth: true } }}
                    disabled={loading}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <DatePicker
                    label="To Date"
                    value={filters.dateTo}
                    onChange={(date) => setFilters({ ...filters, dateTo: date })}
                    slotProps={{ textField: { fullWidth: true } }}
                    disabled={loading}
                  />
                </Grid>
              </Grid>
            </CardContent>

            <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
              <Button
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
                disabled={loading}
              >
                Clear Filters
              </Button>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
                onClick={generateJobsReport}
                disabled={loading}
              >
                Generate Report
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Report Types Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Available Reports
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Jobs Report
              </Typography>
              <Typography variant="body2" paragraph>
                Includes:
              </Typography>
              <ul style={{ marginTop: 0 }}>
                <li>List of all jobs matching the filter criteria</li>
                <li>Customer information</li>
                <li>Job dates and status</li>
                <li>Number of devices per job</li>
                <li>Revenue calculations</li>
                <li>Summary statistics</li>
              </ul>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Individual Job Reports
              </Typography>
              <Typography variant="body2">
                Available from the Job Details page, includes:
              </Typography>
              <ul style={{ marginTop: 0 }}>
                <li>Detailed job information</li>
                <li>Complete list of devices</li>
                <li>Custom pricing details</li>
                <li>Daily revenue calculations</li>
              </ul>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              All reports are generated in PDF format and can be downloaded immediately.
              Use the filters to customize the report content based on your needs.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Reports;
