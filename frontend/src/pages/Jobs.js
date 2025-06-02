import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  Grid,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { DatePicker } from '@mui/x-date-pickers';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import axios from 'axios';

function Jobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    dateFrom: null,
    dateTo: null,
  });

  // New job form
  const [newJob, setNewJob] = useState({
    customerID: '',
    statusID: '',
    startDate: null,
    endDate: null,
    description: '',
  });

  const columns = [
    { field: 'jobID', headerName: 'Job ID', width: 100 },
    { field: 'kunde', headerName: 'Customer', width: 200 },
    {
      field: 'startDate',
      headerName: 'Start Date',
      width: 120,
      valueFormatter: (params) => 
        params.value ? new Date(params.value).toLocaleDateString('de-DE') : 'N/A',
    },
    {
      field: 'endDate',
      headerName: 'End Date',
      width: 120,
      valueFormatter: (params) => 
        params.value ? new Date(params.value).toLocaleDateString('de-DE') : 'N/A',
    },
    { field: 'status', headerName: 'Status', width: 120 },
    { field: 'device_count', headerName: 'Devices', width: 100 },
    {
      field: 'final_revenue',
      headerName: 'Revenue',
      width: 120,
      valueFormatter: (params) => 
        params.value ? `€${params.value.toFixed(2)}` : '€0.00',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Button
          variant="contained"
          size="small"
          onClick={() => navigate(`/jobs/${params.row.jobID}`)}
        >
          View
        </Button>
      ),
    },
  ];

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const params = {
        search: filters.search,
        status: filters.status,
        date_from: filters.dateFrom?.toISOString().split('T')[0],
        date_to: filters.dateTo?.toISOString().split('T')[0],
      };

      const response = await axios.get('/api/v1/jobs', { params });
      setJobs(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setError('Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const handleCreateJob = async () => {
    try {
      const response = await axios.post('/api/v1/jobs', {
        ...newJob,
        startDate: newJob.startDate?.toISOString().split('T')[0],
        endDate: newJob.endDate?.toISOString().split('T')[0],
      });

      setOpenDialog(false);
      setNewJob({
        customerID: '',
        statusID: '',
        startDate: null,
        endDate: null,
        description: '',
      });
      
      // Navigate to the new job's detail page
      navigate(`/jobs/${response.data.jobID}`);
    } catch (error) {
      console.error('Error creating job:', error);
      setError('Failed to create job');
    }
  };

  const handleClearFilters = () => {
    setFilters({
      search: '',
      status: '',
      dateFrom: null,
      dateTo: null,
    });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Jobs</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          New Job
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Search"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                label="Status"
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={2}>
            <DatePicker
              label="From Date"
              value={filters.dateFrom}
              onChange={(date) => setFilters({ ...filters, dateFrom: date })}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <DatePicker
              label="To Date"
              value={filters.dateTo}
              onChange={(date) => setFilters({ ...filters, dateTo: date })}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={fetchJobs}
              >
                Search
              </Button>
              <Button
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
              >
                Clear
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Jobs Table */}
      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={jobs}
          columns={columns}
          pageSize={10}
          rowsPerPageOptions={[10]}
          getRowId={(row) => row.jobID}
          loading={loading}
          disableSelectionOnClick
        />
      </Paper>

      {/* Create Job Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Job</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Customer ID"
                value={newJob.customerID}
                onChange={(e) => setNewJob({ ...newJob, customerID: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={newJob.statusID}
                  label="Status"
                  onChange={(e) => setNewJob({ ...newJob, statusID: e.target.value })}
                >
                  <MenuItem value="1">Active</MenuItem>
                  <MenuItem value="2">Completed</MenuItem>
                  <MenuItem value="3">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Start Date"
                value={newJob.startDate}
                onChange={(date) => setNewJob({ ...newJob, startDate: date })}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="End Date"
                value={newJob.endDate}
                onChange={(date) => setNewJob({ ...newJob, endDate: date })}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={4}
                value={newJob.description}
                onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateJob}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Jobs;
