<?php
require_once 'vendor/autoload.php';

use PhpParser\Error;
use PhpParser\NodeDumper;
use PhpParser\ParserFactory;

if ($argc != 2) {
    echo json_encode(['error' => 'Usage: php parse-file.php <file-path>']);
    exit(1);
}

$file = $argv[1];

if (!file_exists($file)) {
    echo json_encode(['error' => 'File not found: ' . $file]);
    exit(1);
}

try {
    $code = file_get_contents($file);
    
    // Use the modern API
    $parserFactory = new ParserFactory();
    $parser = $parserFactory->createForNewestSupportedVersion();
    
    $ast = $parser->parse($code);
    
    $dumper = new NodeDumper(['dumpComments' => true]);
    $astJson = $dumper->dump($ast);
    
    echo json_encode([
        'success' => true,
        'ast' => $astJson,
        'file' => $file
    ]);
} catch (Error $error) {
    echo json_encode([
        'error' => 'Parse error: ' . $error->getMessage(),
        'file' => $file,
        'line' => $error->getStartLine()
    ]);
} catch (Exception $e) {
    echo json_encode([
        'error' => 'General error: ' . $e->getMessage(),
        'file' => $file
    ]);
}
?>
