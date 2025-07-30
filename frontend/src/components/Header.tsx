import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { AutoAwesome } from '@mui/icons-material';

const Header: React.FC = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <AutoAwesome sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          TestPilot AI
        </Typography>
        <Box>
          <Button 
            color="inherit" 
            component={RouterLink} 
            to="/tests"
          >
            Test Management
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 