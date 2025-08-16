import { NextApiRequest, NextApiResponse } from 'next';
import { spawn } from 'child_process';
import path from 'path';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { ticker, action } = req.body;

  if (!ticker || !action) {
    return res.status(400).json({ error: 'Missing ticker or action' });
  }

  if (!['add', 'remove'].includes(action)) {
    return res.status(400).json({ error: 'Invalid action. Must be "add" or "remove"' });
  }

  try {
    // Path to the Python script
    const scriptPath = path.join(process.cwd(), 'add_stock_service.py');
    
    // Execute the Python script
    const pythonProcess = spawn('python3', [scriptPath, action, ticker.toUpperCase()], {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        console.log(`✅ Successfully ${action}ed ${ticker}`);
        console.log('Output:', stdout);
        res.status(200).json({ 
          success: true, 
          message: `Successfully ${action}ed ${ticker}`,
          output: stdout
        });
      } else {
        console.error(`❌ Error ${action}ing ${ticker}:`, stderr);
        res.status(500).json({ 
          error: `Failed to ${action} ${ticker}`,
          details: stderr || stdout
        });
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('Process error:', error);
      res.status(500).json({ 
        error: 'Failed to execute Python script',
        details: error.message
      });
    });

  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
