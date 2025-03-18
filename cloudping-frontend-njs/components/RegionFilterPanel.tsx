'use client';
import { useState, useEffect } from 'react';

interface RegionFilterPanelProps {
  allRegions: string[];
  selectedRegions: string[];
  setSelectedRegions: (regions: string[]) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function RegionFilterPanel({
  allRegions,
  selectedRegions,
  setSelectedRegions,
  isOpen,
  onClose
}: RegionFilterPanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    'Americas': true,
    'Europe': true,
    'Asia Pacific': true,
    'Middle East & Africa': true,
  });

  // Group regions dynamically
  const regionGroups: Record<string, string[]> = {
    'Americas': [],
    'Europe': [],
    'Asia Pacific': [],
    'Middle East & Africa': []
  };
  
  allRegions.forEach(region => {
    const prefix = region.split('-')[0];
    
    switch (prefix) {
      case 'us':
      case 'ca':
      case 'sa':
      case 'mx':
        regionGroups['Americas'].push(region);
        break;
      case 'eu':
        regionGroups['Europe'].push(region);
        break;
      case 'ap':
        regionGroups['Asia Pacific'].push(region);
        break;
      case 'me':
      case 'af':
      case 'il':
        regionGroups['Middle East & Africa'].push(region);
        break;
      default:
        // If unknown, add to all regions only
        console.log(`Unknown region prefix: ${prefix}`);
    }
  });

  // Filter regions by search term
  const getFilteredRegions = (regions: string[]) => {
    if (!searchTerm) return regions;
    return regions.filter(region => 
      region.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  // Handle select all
  const handleSelectAll = () => {
    setSelectedRegions([...allRegions]);
  };

  // Handle clear all
  const handleClearAll = () => {
    setSelectedRegions([]);
  };

  // Toggle region selection
  const toggleRegion = (region: string) => {
    if (selectedRegions.includes(region)) {
      setSelectedRegions(selectedRegions.filter(r => r !== region));
    } else {
      setSelectedRegions([...selectedRegions, region]);
    }
  };

  // Toggle group selection
  const toggleGroup = (groupName: string) => {
    const groupRegions = regionGroups[groupName];
    
    // Check if all regions in this group are already selected
    const allSelected = groupRegions.every(region => selectedRegions.includes(region));
    
    if (allSelected) {
      // Remove all regions in this group
      setSelectedRegions(selectedRegions.filter(region => !groupRegions.includes(region)));
    } else {
      // Add all missing regions from this group
      const regionsToAdd = groupRegions.filter(region => !selectedRegions.includes(region));
      setSelectedRegions([...selectedRegions, ...regionsToAdd]);
    }
  };

  // Toggle group expansion
  const toggleGroupExpansion = (groupName: string) => {
    setExpandedGroups({
      ...expandedGroups,
      [groupName]: !expandedGroups[groupName]
    });
  };

  // Calculate if all regions in a group are selected
  const isGroupAllSelected = (groupName: string) => {
    const groupRegions = regionGroups[groupName];
    return groupRegions.every(region => selectedRegions.includes(region));
  };

  // Calculate if some (but not all) regions in a group are selected
  const isGroupPartiallySelected = (groupName: string) => {
    const groupRegions = regionGroups[groupName];
    const selectedCount = groupRegions.filter(region => selectedRegions.includes(region)).length;
    return selectedCount > 0 && selectedCount < groupRegions.length;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end">
      <div className="bg-zinc-800 w-96 h-full shadow-lg overflow-y-auto">
        <div className="p-4 border-b border-zinc-700 flex justify-between items-center">
          <h2 className="text-lg font-medium text-white">Region Filter</h2>
          <button 
            onClick={onClose}
            className="text-zinc-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="p-4">
          <div className="mb-4 flex">
            <input
              type="text"
              placeholder="Search regions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 bg-zinc-700 text-white border border-zinc-600 rounded-l px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
            <button 
              onClick={() => setSearchTerm('')}
              className="bg-zinc-700 text-zinc-400 border border-l-0 border-zinc-600 rounded-r px-3 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="mb-4 flex gap-2">
            <button
              onClick={handleSelectAll}
              className="bg-zinc-700 hover:bg-zinc-600 text-white rounded px-3 py-1 text-sm"
            >
              Select All
            </button>
            <button
              onClick={handleClearAll}
              className="bg-zinc-700 hover:bg-zinc-600 text-white rounded px-3 py-1 text-sm"
            >
              Clear All
            </button>
            <div className="ml-auto text-sm text-zinc-400">
              {selectedRegions.length} of {allRegions.length} selected
            </div>
          </div>

          <div className="space-y-4">
            {Object.entries(regionGroups).map(([groupName, regions]) => {
              const filteredRegions = getFilteredRegions(regions);
              if (filteredRegions.length === 0 && searchTerm) return null;
              
              return (
                <div key={groupName} className="border border-zinc-700 rounded">
                  <div 
                    className="flex items-center p-3 cursor-pointer hover:bg-zinc-700"
                    onClick={() => toggleGroupExpansion(groupName)}
                  >
                    <input
                      type="checkbox"
                      checked={isGroupAllSelected(groupName)}
                      ref={el => {
                        if (el) {
                          el.indeterminate = isGroupPartiallySelected(groupName);
                        }
                      }}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleGroup(groupName);
                      }}
                      className="mr-2 h-4 w-4"
                    />
                    <span className="text-white font-medium flex-1">
                      {groupName} ({filteredRegions.length})
                    </span>
                    <span className="text-zinc-400">
                      {expandedGroups[groupName] ? '▼' : '►'}
                    </span>
                  </div>
                  
                  {expandedGroups[groupName] && filteredRegions.length > 0 && (
                    <div className="border-t border-zinc-700 p-2 pl-8 space-y-1 bg-zinc-800">
                      {filteredRegions.map(region => (
                        <div key={region} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`region-${region}`}
                            checked={selectedRegions.includes(region)}
                            onChange={() => toggleRegion(region)}
                            className="mr-2 h-4 w-4"
                          />
                          <label 
                            htmlFor={`region-${region}`}
                            className="text-zinc-300 text-sm cursor-pointer"
                          >
                            {region}
                          </label>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}