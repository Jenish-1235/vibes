package executor

import (
	"testing"
)

func TestIdeBinary_KnownTools(t *testing.T) {
	tests := []struct {
		tool     string
		expected string
	}{
		{"cursor", "cursor"},
		{"vscode", "code"},
		{"code", "code"},
		{"zed", "zed"},
		{"idea", "idea"},
	}

	for _, tc := range tests {
		bin, err := ideBinary(tc.tool)
		if err != nil {
			t.Errorf("ideBinary(%q) unexpected error: %v", tc.tool, err)
		}
		if bin != tc.expected {
			t.Errorf("ideBinary(%q) = %q, want %q", tc.tool, bin, tc.expected)
		}
	}
}

func TestIdeBinary_UnknownTool(t *testing.T) {
	_, err := ideBinary("notepad")
	if err == nil {
		t.Error("expected error for unknown IDE tool")
	}
}
